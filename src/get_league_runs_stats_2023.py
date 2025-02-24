import datetime
import os
import time

import pandas as pd
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
LEAGUE_HACKS_FILE = 'league_hacks.json'
load_dotenv()
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
MY_WEBHOOK_URL = os.getenv('MY_WEBHOOK_URL')
FANTASY_SPREADSHEET_ID = os.getenv('FANTASY_SPREADSHEET_ID')
runs_file = '2024_runs.json'


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


def get_new_runs(last_ran_date, run_date, last_submit_date):
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
                        if dt.strptime(submit_date, '%Y-%m-%dT%H:%M:%SZ') <= last_submit_date:
                            print(run)
                            primary_time = run['times']['primary']
                            cur_player = run['players']['data'][0]
                            if cur_player['rel'] == 'user':
                                player_id = cur_player['id']
                                player_name = cur_player['names']['international']
                            else:
                                player_id = None
                                player_name = cur_player['name']
                            player_name = player_name.replace('ñ', 'n').lower()
                            current_run['game'] = hack['name']
                            current_run['category'] = cat['name']
                            current_run['time'] = primary_time
                            current_run['act_time'] = run['times']['primary_t']
                            current_run['player'] = player_name
                            current_run['player_id'] = player_id
                            current_run['verify-date'] = verified_date
                            current_run['date'] = run['date']
                            current_run['verifier'] = run['status']['examiner']
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


def lambda_handler(event, context):
    run_time = dt.strptime(dt.now(tz=datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), '%Y-%m-%dT%H:%M:%SZ')
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    document = service.spreadsheets()
    config = get_config(document, SPREADSHEET_ID)
    start_date = config[0][1]
    last_submit_date = config[0][2]
    new_runs = get_new_runs(dt.strptime(start_date, '%Y-%m-%d'), run_time, dt.strptime(
        last_submit_date, '%Y-%m-%dT%H:%M:%SZ'))



    with open(runs_file, 'w') as f:
        json.dump(new_runs, f)

    analyze_runs = None

    with open(runs_file, 'r') as file:
        analyze_runs = json.load(file)

    print(analyze_runs)

    df = pd.DataFrame(analyze_runs)
    print(df)
    #print(df.groupby(['game','category']).count())
    print(df.groupby(['game']).count())
    print(df.groupby(['game','category']).count())
    #print(df['verifier'].groupby(['verifier'].count().reset_index(name='count').sort_values(['count'], ascending=False)))
    #print(df.groupby(['player'].count().reset_index(name='count').sort_values(['count'], ascending=False)))

    df2 = df[['verifier']].groupby(['verifier'])['verifier'] \
        .count() \
        .reset_index(name='count') \
        .sort_values(['count'], ascending=False) \
        .head(5)
    print(df2)
    df3 = df[['player']].groupby(['player'])['player'] \
        .count() \
        .reset_index(name='count') \
        .sort_values(['count'], ascending=False) \
        .head(20)
    print(df3)

    return {
        'statusCode': 200,
        'body': 'Run Complete'
    }


if __name__ == '__main__':
    print(lambda_handler(1, 2))
