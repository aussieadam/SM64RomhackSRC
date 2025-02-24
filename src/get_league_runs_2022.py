import datetime
import os
import time

from discord import SyncWebhook

import requests
import json
import argparse
from datetime import datetime as dt, timedelta
from dotenv import load_dotenv
from table2ascii import table2ascii as t2a, PresetStyle
from googleapiclient.discovery import build
from google.oauth2 import service_account

_HEADERS = {
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'User-Agent': 'league-leaderboards/1.0',
    'Accept': '*/*',
}
_h = dict(_HEADERS)
_sleep_period = .75
_retry_sleep = 30

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'credentials.json'
LEAGUE_HACKS_FILE = 'league_hacks_2023.json'
load_dotenv()
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
MY_WEBHOOK_URL = os.getenv('MY_WEBHOOK_URL')


# url help
def get_runs_for_game_category(game_id, category):
    return f'https://www.speedrun.com/api/v1/runs?game={game_id}&category={category}&status=verified&orderby=verify-date&direction=desc&embed=players'


def get_leaderboard_for_game_category(game_id, category):
    return f'https://www.speedrun.com/api/v1/leaderboards/{game_id}/category/{category}?embed=players'


def get_runs_for_game(game_id):
    return f'https://www.speedrun.com/api/v1/runs?game={game_id}&status=verified&orderby=verify-date&direction=desc'


def get_romhacks():
    return f'https://www.speedrun.com/api/v1/series/0499o64v/games?max=200'


def valid_date(s):
    try:
        return dt.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        msg = "not a valid date: {0!r}".format(s)
        raise argparse.ArgumentTypeError(msg)


def request_src(url):
    err_lim = 5
    err_cnt = 1
    request_finished = False
    resp = None
    # print(f"attempting to request from:{url}")
    # usually fails if we are requesting too quickly, even with the sleep, try 10 times fail if still not working
    # after 10
    while not request_finished and err_cnt <= err_lim:
        # print(f"attempt: {err_cnt}")
        try:
            resp = requests.get(url, headers=_h)
            request_finished = True
            # print("request finished")
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            print(f"Error Getting Response from {url}")
            print(e)
            if err_cnt == err_lim:
                raise requests.exceptions.RequestException
            err_cnt += 1
            print(f"sleeping for {_retry_sleep} before retry")
            time.sleep(_retry_sleep)
            print("retrying")
    # probably redundant, just being careful
    if err_cnt >= err_lim:
        print(f"err_cnt greater than err_limit {err_cnt} >= {err_lim}")
        raise requests.exceptions.RequestException
    # sleep so we don't get banned by requesting too much, .1,.2 give errors after doing a few hundred
    time.sleep(_sleep_period)
    if resp is not None and resp.status_code == 200:
        return resp.json()
    elif resp.status_code != 200:
        raise requests.exceptions.RequestException
    else:
        return None


def get_new_runs(last_ran_date, run_date,last_submit_date):
    hacks = json.load(open(LEAGUE_HACKS_FILE))
    runs = []
    for hack in hacks:
        for category in hack['categories']:
            cat = category
            category_runs = []
            category_players = {}
            url = get_runs_for_game_category(hack['id'], category['id'])
            while url is not None:
                res = request_src(url)
                # print(url)
                for run in res['data']:
                    current_run = {}
                    # get date of verified so we can compare if we've already seen this run
                    verified_date = run['status']['verify-date']
                    submit_date = run['submitted']
                    lr_date_safety = last_ran_date - timedelta(
                        hours=3)
                    # print(run)
                    # print(lr_date_safety)
                    # print(verified_date)
                    # print(run_date)
                    if verified_date is not None and lr_date_safety <= dt.strptime(verified_date,
                                                                                   '%Y-%m-%dT%H:%M:%SZ') < run_date:
                        if dt.strptime(submit_date,'%Y-%m-%dT%H:%M:%SZ') <= last_submit_date:
                            print(run)
                            primary_time = run['times']['primary']
                            cur_player = run['players']['data'][0]
                            if cur_player['rel'] == 'user':
                                player_id = cur_player['id']
                                player_name = cur_player['names']['international']
                            else:
                                player_id = None
                                player_name = cur_player['name']
                            player_name = player_name.replace('ñ', 'n')
                            current_run['game'] = hack['name']
                            current_run['category'] = cat
                            current_run['time'] = primary_time
                            current_run['act_time'] = run['times']['primary_t']
                            current_run['player'] = player_name
                            current_run['player_id'] = player_id
                            current_run['verify-date'] = verified_date
                            current_run['date'] = run['date']
                            if player_name not in category_players:
                                category_players[current_run['player']] = current_run['act_time']
                                category_runs.append(current_run)
                            else:
                                if category_players[current_run['player']] > current_run['act_time']:
                                    category_players[current_run['player']] = current_run['act_time']

                                    for cat_run in category_runs:
                                        if cat_run['player'] == player_name:
                                            if cat_run['act_time'] > current_run['act_time']:
                                                category_runs.remove(cat_run)
                                                category_runs.append(current_run)

                    else:
                        url = None
                        break
                # if the last run of page isn't before the last time this ran, keep paginating
                if url is not None:
                    url = None
                    for page in res['pagination']['links']:
                        if page['rel'] == 'next':
                            url = page['uri']
            runs.extend(category_runs)
    return runs


def get_participants(doc, spreadsheet_id, participant_range):
    participants_sheet = doc.values().get(
        spreadsheetId=spreadsheet_id, range=participant_range
    ).execute()
    participants_list = participants_sheet.get('values', [])
    row = 2
    parts={}
    for part in participants_list:
        parts[part[1].lower()] = row
        row=row+1

    return parts


def get_sheets(doc, spreadsheet_id):
    sheets_dict = {}
    sheets = doc.get(
        spreadsheetId=spreadsheet_id, includeGridData=False
    ).execute()
    for sheet in sheets['sheets']:
        sheets_dict[sheet['properties']['title']] = sheet['properties']['sheetId']
    return sheets_dict


def get_config(doc, spreadsheet_id):
    config_sheet = doc.values().get(
        spreadsheetId=spreadsheet_id, range="config!A2:D2"
    ).execute()
    return config_sheet.get('values', [])


def update_times(doc, spreadsheet_id, parts, runs, start_dt):
    data_range = 'B6:P7'

    batch_update_body = {
        "data": [],
        "value_input_option": "USER_ENTERED"
    }
    for run in runs:
        player = run['player'].lower().strip()
        if player in parts:
            # print(run)
            # run_final_time = time.gmtime(run['act_time'])
            run_final_time = run['act_time']
            player_range = 'participants' + "!" + run['category']['column'] + str(parts[player])
            values = [[run_final_time]]

            value_range_body = {
                "majorDimension": "COLUMNS",
                "values": values,
                "range": player_range
            }
            batch_update_body['data'].append(value_range_body)

    if len(batch_update_body['data']) > 0:
        resp = doc.values().batchUpdate(spreadsheetId=spreadsheet_id,
                                        body=batch_update_body).execute()


def update_leaderboard(doc, spreadsheet_id, parts, parts_range):
    user_leaderboard = []
    team_leaderboard = {}
    value_render_option = 'FORMATTED_VALUE'

    part_data_list = doc.values().batchGet(spreadsheetId=spreadsheet_id, ranges=parts_range,
                                           valueRenderOption=value_render_option).execute()

    for part_data in part_data_list['valueRanges']:
        print(part_data)
        team = part_data['values'][0][0].strip()
        if team is None or team == '':
            team = 'undrafted'
        score = part_data['values'][0][1]
        user_points = {
            "user": part_data['range'].split('!')[0],
            "team": team,
            "score": int(score)
        }

        if team in team_leaderboard:
            team_leaderboard[team] = int(score) + team_leaderboard[team]
        else:
            team_leaderboard[team] = int(score)
        user_leaderboard.append(user_points)

    user_leaderboard.sort(key=lambda k: k['score'], reverse=True)
    team_leaderboard = dict(sorted(team_leaderboard.items(), key=lambda item: item[1], reverse=True))

    team_range = 'Team Leaderboard!A2:B10'
    user_range = 'User Leaderboard!A2:C100'

    batch_leaderboard_body = {
        "data": [],
        "value_input_option": "USER_ENTERED"
    }

    user_range_body = {
        "majorDimension": "ROWS",
        "values": [],
        "range": user_range
    }

    for user in user_leaderboard:
        user_range_body["values"].append([user['user'], user['team'], user['score']])

    batch_leaderboard_body['data'].append(user_range_body)
    team_range_body = {
        "majorDimension": "ROWS",
        "values": [],
        "range": team_range
    }
    for key, value in team_leaderboard.items():
        team_range_body["values"].append([key, value])
    batch_leaderboard_body['data'].append(team_range_body)

    resp = doc.values().batchUpdate(spreadsheetId=spreadsheet_id,
                                    body=batch_leaderboard_body).execute()

    return [user_leaderboard, team_leaderboard]


def update_discord(boards, race_boards):
    user_boards = boards[0]
    team_boards = boards[1]
    team_body = []
    user_body = []
    race_body = []

    race_rank_cnt = 1
    for res in race_boards:
        if race_rank_cnt > 10:
            break
        race_body.append([race_rank_cnt, res['runner'], res['total_points'], res['average_points']])
        race_rank_cnt = race_rank_cnt + 1

    user_rank_cnt = 1
    for user in user_boards:
        if user_rank_cnt > 30:
            break
        user_body.append([user_rank_cnt, user['team'], user['user'], user['score']])
        user_rank_cnt = user_rank_cnt + 1

    team_rank_cnt = 1
    for team, score in team_boards.items():
        if team_rank_cnt > 6:
            break
        team_body.append([team_rank_cnt, team, score])
        team_rank_cnt = team_rank_cnt + 1

    team_discord_leaderboard = t2a(
        header=["PLACE", "TEAM", "SCORE"],
        body=team_body,
        first_col_heading=True,
        style=PresetStyle.thin_compact
    )
    print(team_discord_leaderboard)
    user_discord_leaderboard = t2a(
        header=["PLACE", "TEAM", "USER", "SCORE"],
        body=user_body,
        first_col_heading=True,
        style=PresetStyle.thin_compact
    )
    print(user_discord_leaderboard)

    race_discord_leaderboard = t2a(
        header=["PLACE", "USER", "TOTAL_SCORE", "AVERAGE_SCORE"],
        body=race_body,
        first_col_heading=True,
        style=PresetStyle.thin_compact
    )
    print(user_discord_leaderboard)

    return [user_discord_leaderboard, team_discord_leaderboard, race_discord_leaderboard]


def get_race_results(doc, spreadsheet_id, races_range, parts):
    race_points_list = []
    all_race_points_list = []
    sheets = doc.get(spreadsheetId=spreadsheet_id).execute()['sheets']
    race_ids = []
    for sheet in sheets:
        if ' Race ' in sheet['properties']['title']:
            race_ids.append(sheet['properties']['title'])

    race_sheet_range = []
    value_render_option = 'FORMATTED_VALUE'
    for race_id in race_ids:
        race_sheet_range.append(race_id + "!" + races_range)

    race_data_list = doc.values().batchGet(spreadsheetId=spreadsheet_id, ranges=race_sheet_range,
                                           valueRenderOption=value_render_option).execute()

    for race in race_data_list['valueRanges']:
        race_name = race['range'].split('!')[0].replace("'", '')
        for race_result in race['values']:
            if len(race_result) >= 2 and race_result[0] not in ('wr', '') and race_result[0] in parts:
                runner = race_result[0]
                race_points = int(race_result[-1])
                runner_found = False
                all_race_points_list.append({'runner': runner, 'points': race_points, 'race': race_name})
                for race_runner in race_points_list:
                    if race_runner['runner'] == runner:
                        if race_runner['points'] > race_points:
                            runner_found = True
                        else:
                            race_runner['points'] = race_points
                            race_runner['race'] = race_name
                            runner_found = True
                if not runner_found:
                    race_points_list.append({'runner': runner, 'points': race_points, 'race': race_name})

    return [race_points_list, all_race_points_list]


def update_races(doc, spreadsheet_id, race_results):
    update_race_range = 'B13:B14'
    batch_update_body = {
        "data": [],
        "value_input_option": "USER_ENTERED"
    }
    for race_res in race_results:
        player_range = race_res['runner'] + "!" + update_race_range
        values = [[race_res['race']], [race_res['points']]]
        value_range_body = {
            "majorDimension": "ROWS",
            "values": values,
            "range": player_range
        }
        batch_update_body['data'].append(value_range_body)
    if len(batch_update_body['data']) > 0:
        resp = doc.values().batchUpdate(spreadsheetId=spreadsheet_id,
                                        body=batch_update_body).execute()
        print(resp)


def update_race_leaderboards(doc, spreadsheet_id, race_results, race_range):
    race_leaderboard = []
    for race_res in race_results:
        runner = race_res['runner']
        points = race_res['points']
        player_found = False
        for race_runner in race_leaderboard:

            if race_runner['runner'] == runner:
                race_runner['total_points'] += points
                race_runner['run_count'] += 1
                race_runner['average_points'] = round((race_runner['total_points'] / race_runner['run_count']), 2)
                if race_runner['max_points'] > points:
                    player_found = True
                else:
                    race_runner['max_points'] = points
                    player_found = True
        if not player_found:
            race_leaderboard.append({'runner': runner, 'total_points': points, 'run_count': 1, 'average_points': points,
                                     'max_points': points})

    race_leaderboard.sort(key=lambda k: k['total_points'], reverse=True)

    batch_leaderboard_body = {
        "data": [],
        "value_input_option": "USER_ENTERED"
    }

    race_range_body = {
        "majorDimension": "ROWS",
        "values": [],
        "range": race_range
    }
    for user in race_leaderboard:
        race_range_body["values"].append(
            [user['runner'], user['total_points'], user['average_points'], user['max_points']])
    batch_leaderboard_body['data'].append(race_range_body)

    resp = doc.values().batchUpdate(spreadsheetId=spreadsheet_id,
                                    body=batch_leaderboard_body).execute()
    print(resp)
    return race_leaderboard


def edit_leaderboards(boards):
    user_discord_leaderboard = boards[0]
    team_discord_leaderboard = boards[1]
    race_discord_leaderboard = boards[2]
    webhook = SyncWebhook.from_url(WEBHOOK_URL)
    # webhook.send(content=f"```\n{user_discord_leaderboard}\n```")
    # webhook.send(content=f"```\n{team_discord_leaderboard}\n```")

    # webhook.edit_message(message_id=1021028259225411604, content=f"```\n{user_discord_leaderboard}\n```")
    # webhook.edit_message(message_id=1021028260563394590,
    #                      content=f"```\n{team_discord_leaderboard}\n```" + "\n" + f"last updated: <t:{int(time.time())}:f>")

    my_webhook = SyncWebhook.from_url(MY_WEBHOOK_URL)
    my_webhook.edit_message(message_id=1020427613954637874, content=f"```\n{race_discord_leaderboard}\n```")
    my_webhook.edit_message(message_id=1020427615439425696, content=f"```\n{user_discord_leaderboard}\n```")
    my_webhook.edit_message(message_id=1035644907966169220,
                            content=f"```\n{team_discord_leaderboard}\n```" + "\n" + f"last updated: <t:{int(time.time())}:f>")


def update_config(doc, spreadsheet_id, ran_time):
    batch_update_body = {
        "data": [],
        "value_input_option": "USER_ENTERED"
    }

    config_update_body = {
        "majorDimension": "COLUMNS",
        "values": [[ran_time.strftime('%Y-%m-%dT%H:%M:%SZ')]],
        "range": 'config!A2'
    }

    batch_update_body['data'].append(config_update_body)
    resp = doc.values().batchUpdate(spreadsheetId=spreadsheet_id,
                                    body=batch_update_body).execute()
    print(resp)


# def lambda_handler(event, context):
if __name__ == '__main__':
    run_time = dt.strptime(dt.now(tz=datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), '%Y-%m-%dT%H:%M:%SZ')
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    document = service.spreadsheets()
    config = get_config(document, SPREADSHEET_ID)
    last_run_date = config[0][0]
    start_date = config[0][1]
    last_submit_date = config[0][2]
    part_range = "participants!A2:S200"
    participants = get_participants(document, SPREADSHEET_ID, part_range)
    new_runs = get_new_runs(dt.strptime(last_run_date, '%Y-%m-%dT%H:%M:%SZ'), run_time,
                             dt.strptime(last_submit_date, '%Y-%m-%dT%H:%M:%SZ'))
    update_times(document, SPREADSHEET_ID, participants, new_runs, start_date)


    score_leaderboards = update_leaderboard(document, SPREADSHEET_ID, participants,part_range)
    #
    # l_boards = update_discord(score_leaderboards, race_leaderboards)
    #
    # edit_leaderboards(l_boards)
    #
    # update_config(document, SPREADSHEET_ID, run_time)
    #
    # return {
    #     'statusCode': 200,
    #     'body': 'Run Complete'
    # }
