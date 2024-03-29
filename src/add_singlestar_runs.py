import argparse
import time
import dcd.SRCHelper as srcHelper
import json
import os
from dotenv import load_dotenv
import pandas as pd

# need to run get_romhacks.py first, you could couple them together, but I prefer separating, so I can use hacks.json
# elsewhere without having to run a long method everytime
start_time = time.time()

parser = argparse.ArgumentParser(description="Add Single Star runs parser")

parser.add_argument('--stars', required=False, type=str, default='stars_list.xlsx',
                    help='game to get runs from')
parser.add_argument('--hacks', required=False, type=str, default='hacks.json',
                    help='Hack list json')
parser.add_argument('--live', required=False, type=str, default='False',
                    help='is this a live run? if you want to try to add these to SRC turn to true, else be false and '
                         'just print what it would add')
args = parser.parse_args()

load_dotenv()
run_list = args.stars
hack_list = args.hacks
live_run = True if args.live.lower() == 'true' else False
print(f"Live run set to: {live_run}")
# expects a .env file with SRC_API_KEY, you can get the key from https://www.speedrun.com/<YOUR_USER_HERE>/settings/api
SRC_API_KEY = os.getenv('SRC_API_KEY')


def get_secs(time_str):
    split = time_str.split(':')
    if len(split) == 3:
        h, m, s = split
    elif len(split) == 2:
        h = 0
        m, s = split
    else:
        h = 0
        m = 0
        s = split[0]
    return int(h) * 3600 + int(m) * 60 + float(s)


def get_star_details(game_name, ss_star_name, level_name=None):
    hacks = json.load(open(hack_list))
    stars_list = []
    ss_cat_id = None
    for hack in hacks:
        if hack['name'].lower() == game_name.lower():
            if 'Single Star' in hack['categories']:
                ss_cat_id = hack['categories']['Single Star']
            elif 'Single Stars' in hack['categories']:
                ss_cat_id = hack['categories']['Single Stars']
            elif 'Single Shines' in hack['categories']:
                ss_cat_id = hack['categories']['Single Shines']
            elif 'Stars' in hack['categories']:
                ss_cat_id = hack['categories']['Stars']
            elif 'Single Burger' in hack['categories']:
                ss_cat_id = hack['categories']['Single Burger']
            elif 'INDIVIDUAL LEVELS' in hack['categories']:
                ss_cat_id = hack['categories']['INDIVIDUAL LEVELS']
            elif 'Star Speedruns' in hack['categories']:
                ss_cat_id = hack['categories']['Star Speedruns']
            record = {}
            # this is really stupid, SRC wants a list of all variables, even if they are unused, so we have to go
            # through and set them all, but also make sure we set the right variable
            # first if is for if we defined a level name(hopefully did)
            if level_name is not None:
                for variable_id, variables in hack['variables'].items():
                    if variable_id.lower() == level_name.lower():
                        for val_id, val in variables['choices'].items():
                            if val.lower() == ss_star_name.lower():
                                record['final_record'] = [hack['id'], variables['id'], variables['level_id'],
                                                          val_id, ss_cat_id]
                    else:
                        for val_id, val in variables['choices'].items():
                            record[variables['id']] = {"type": "pre-defined", "value": val_id}
                            break
            else:
                for variable_id, variables in hack['variables'].items():
                    found_star_in_var = False
                    for val_id, val in variables['choices'].items():
                        if val.lower() == ss_star_name.lower():
                            found_star_in_var = True
                            record['final_record'] = [hack['id'], variables['id'], variables['level_id'],
                                                      val_id, ss_cat_id]
                    if not found_star_in_var:
                        for val_id, val in variables['choices'].items():
                            record[variables['id']] = {"type": "pre-defined", "value": val_id}
                            break
            stars_list.append(record)
            break
    return stars_list


if __name__ == '__main__':
    run_data = []
    read_file = pd.read_excel(run_list, keep_default_na=False)
    no_matching_stars = []
    missing_star_category = []
    missing_star_or_level = []
    multiple_matching_stars = []
    missing_urls = []
    missing_users = []
    users = {}
    for index, run in read_file.iterrows():
        # only want to upload video proof
        hack_name = run['Rom Hack Name']
        course_name = run['Course Name']
        star_name = run['Star Name']
        user_name = run['Runner']
        if 'Type of Proof' in run and run['Type of Proof'] != 'Video':
            continue
        # check that the course name is filled out, ideally it always is, but we can search for stars without it
        if run['Course Name'] is not None and run['Course Name'] not in ['', 'nan']:
            game_res = get_star_details(game_name=hack_name, ss_star_name=star_name, level_name=course_name)
        else:
            game_res = get_star_details(game_name=hack_name, ss_star_name=star_name)
        # did not return a game
        if len(game_res) == 0 or game_res is None:
            if hack_name not in no_matching_stars:
                no_matching_stars.append(hack_name)
            continue
        # multiple stars with same name
        if len(game_res) > 1:
            multiple_matching_stars.append([hack_name, star_name])
            continue

        game_res = game_res[0]
        if 'final_record' not in game_res:
            # course or star not in game_res
            missing_star_or_level.append([hack_name, course_name, star_name])
            continue
        final_res = game_res['final_record']
        game_id = final_res[0]
        var_id = final_res[1]
        level_id = final_res[2]
        star_id = final_res[3]
        cat_id = final_res[4]
        del game_res['final_record']

        if cat_id is None:
            # hack missing single stars, or the name of single star category isn't in get_game_level_star body
            missing_star_category.append([hack_name, course_name, star_name])
            continue

        # people without an SRC profile can still be added, these are hardcoded in SRCHelper
        if user_name.replace(" ", "") in srcHelper.NON_SRC_USERS:
            user_id = user_name.replace(" ", "")
        # try not to do an extra SRC call if we've already gotten back this persons' user_id
        elif user_name in users:
            user_id = users[user_name]
        else:
            user_url = srcHelper.get_user(user_name)
            user_res = srcHelper.request_src(user_url)
            if 'status' in user_res and user_res['status'] == 404:
                missing_users.append(user_name)
                continue
            else:
                user_id = user_res['data']['id']
            users[user_name] = user_id



        # check the proof if YouTube vid, if not, check if there's a backup video
        if run['Proof'] is not None and ('youtube' in run['Proof'] or 'youtu.be' in run['Proof'] or 'twitch.tv' in run['Proof']):
            run_url = run['Proof']
        elif 'Backup Video' in run and run['Backup Video'] is not None and run['Backup Video'] not in ['', 'nan'] and (
                'youtube' in run['Backup Video'] or 'youtu.be' in run['Backup Video']):
            run_url = run['Backup Video']
        else:
            missing_urls.append([hack_name, course_name, star_name, user_name])
            continue

        run_time = get_secs(str(run['Time']))
        run_date = run['Date'].strftime('%Y-%m-%d')
        run_json = {'game_id': game_id, 'cat_id': cat_id, 'user_id': user_id, 'run_time': run_time,
                    'run_date': run_date, 'run_url': run_url, 'level_id': level_id, 'star_id': star_id,
                    'var_id': var_id, 'stupid_vars': game_res}

        # check this run isn't already on SRC
        runs_by_user_game_cat_url = srcHelper.get_runs_by_user_game_cat(user_id, game_id, cat_id)
        found_run = False
        # if the user has a lot of runs for this game it will paginate the results, max is 200, it'd be very rare,
        # but this could catch an edge case
        while runs_by_user_game_cat_url is not None:
            runs_by_user_game_cat = srcHelper.request_src(runs_by_user_game_cat_url)
            for urn in runs_by_user_game_cat['data']:
                if level_id == urn['level'] and star_id == urn['values'][var_id]:
                    if urn['times']['primary_t'] <= run_time:
                        found_run = True
                        runs_by_user_game_cat_url = None
                        break

            # if the last run of page isn't before the last time this ran, keep paginating
            if runs_by_user_game_cat_url is not None:
                runs_by_user_game_cat_url = None
                for page in runs_by_user_game_cat['pagination']['links']:
                    if page['rel'] == 'next':
                        runs_by_user_game_cat_url = page['uri']

        # add run if not on SRC
        if not found_run:
            run_data.append(run_json)

    for run in run_data:
        add_run_request_body = srcHelper.get_singlestar_run_body(run['user_id'], run['cat_id'], run['run_time'],
                                                                 run['run_date'],
                                                                 'w89rwelk', True, run['run_url'], run['level_id'],
                                                                 run['var_id'], run['star_id'], run['stupid_vars'])

        if live_run:
            runs_url = srcHelper.get_runs_url()
            post_src_res = srcHelper.post_src(runs_url, add_run_request_body, SRC_API_KEY)
            print(post_src_res)
        else:
            print(add_run_request_body)

    # print all the issues, i separated them out into lists
    for multiple_match in multiple_matching_stars:
        print(f'hack: {multiple_match[0]} has multiple stars named : {multiple_match[1]}')

    for non_matching in no_matching_stars:
        print(f'hack: {non_matching} does not exist on SRC')

    for missing_star_cat in missing_star_category:
        print(
            f'hack: {missing_star_cat[0]}, has no single star category within SRC or get_game_level_star is missing '
            f'single star category')

    for missing in missing_star_or_level:
        print(f'hack: {missing[0]} is missing course: {missing[1]} or star: {missing[2]} on SRC')

    for run in missing_urls:
        print(f'Hack {run[0]}: Course {run[1]}: Star {run[2]}: for {run[3]} missing youtube video proof')

    for user in missing_users:
        print(f'{user}:  missing from SRC')

    print(f"---Finished in {(time.time() - start_time)} seconds ---")
