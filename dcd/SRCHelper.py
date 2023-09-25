import time

import requests

# stole these from firefox, default headers were redirecting too many times
_HEADERS = {
    'Host': 'www.speedrun.com',
    'User-Agent': 'src-stats/1.0',
    'Upgrade-Insecure-Requests': '1',
    'TE': 'trailers',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none'
}
_h = dict(_HEADERS)
_sleep_period = .75
_retry_sleep = 30

NON_SRC_USERS = ['Maha Maha', 'Cryogeon', 'Madghostek', 'WWMResident','atmpas','CeeSZee','255']


# url help
def get_runs_url():
    return 'https://www.speedrun.com/api/v1/runs'


def get_runs_for_game_category(game_id, category):
    return f'https://www.speedrun.com/api/v1/runs?game={game_id}&category={category}&status=verified&orderby=verify' \
           f'-date&direction=desc&embed=players'


def get_leaderboard_for_game_category(game_id, category):
    return f'https://www.speedrun.com/api/v1/leaderboards/{game_id}/category/{category}?embed=players'


def get_wr_for_game_category(game_id, category):
    return f'https://www.speedrun.com/api/v1/leaderboards/{game_id}/category/{category}?top=1&embed=players'


def get_runs_for_game(game_id):
    return f'https://www.speedrun.com/api/v1/runs?game={game_id}&status=verified&orderby=verify-date&direction=desc'


def get_romhacks():
    return f'https://www.speedrun.com/api/v1/series/0499o64v/games?max=200&embed=categories,variables,levels'


def get_user(user_id):
    return f'https://www.speedrun.com/api/v1/users/{user_id}'


def post_run():
    return f'https://www.speedrun.com/api/v1/runs/'


def get_level(level_id):
    return f'https://www.speedrun.com/api/v1/levels/{level_id}'


def get_game_variables(game_id):
    return f'https://www.speedrun.com/api/v1/games/{game_id}/variables'


def get_game_id(game):
    return f'https://www.speedrun.com/api/v1/games?name={game}'


def get_game_categories(game_id):
    return f'https://www.speedrun.com/api/v1/games/{game_id}/categories'


def get_runs_by_user_game_cat(user_id, game_id, cat_id):
    return f'https://www.speedrun.com/api/v1/runs?user={user_id}&game={game_id}&category={cat_id}&max=200'


def get_fullgame_run_body(user_id, run_time, date, platform_id, emulated, video_link, category_id):
    return {'run': {
        "category": category_id,
        "date": date,
        "platform": platform_id,
        "verified": True,
        "times": {
            "realtime": run_time
        },
        "players": [
            {"rel": "user", "id": user_id}
        ],
        "emulated": emulated,
        "video": video_link,
        "comment": "Mod Note: Auto-added via api from AussieAdam,please reach out to aussieadam on speedrun.com or "
                   "Aussieadam#0001 for any questions or issues"
    }}


def get_fullgame_variable_run_body(user_id, run_time, date, platform_id, emulated, video_link, var_id, var_val_id,
                                   category_id):
    return {'run': {
        "category": category_id,
        "date": date,
        "platform": platform_id,
        "verified": True,
        "times": {
            "realtime": run_time
        },
        "players": [
            {"rel": "user", "id": user_id}
        ],
        "emulated": emulated,
        "video": video_link,
        "comment": "Mod Note: Auto-added via api from AussieAdam,please reach out to aussieadam on speedrun.com or "
                   "Aussieadam#0001 for any questions or issues",
        "variables": {
            var_id: {
                "type": "pre-defined",
                "value": var_val_id
            }
        }
    }}


def get_singlestar_run_body(user_id, category_id, run_time, date, platform_id, emulated, video_link, level_id, var_id,
                            star_id, stupid_vars):
    rel = 'user'
    id_param = "id"
    # probably do something less dumb
    if user_id in NON_SRC_USERS:
        rel = 'guest'
        id_param = "name"
    run = {'run': {
        "category": category_id,
        "level": level_id,
        "date": date,
        "platform": platform_id,
        "verified": True,
        "times": {
            "realtime": run_time
        },
        "players": [
            {"rel": rel, id_param: user_id}
        ],
        "emulated": emulated,
        "video": video_link,
        "comment": "Mod Note: Auto-added via api from AussieAdam, please reach out to aussieadam on speedrun.com or "
                   "Aussieadam#0001 for any questions or issues",
        "variables": {
            var_id: {
                "type": "pre-defined",
                "value": star_id
            }
        }
    }}
    for var_id, var_value in stupid_vars.items():
        run['run']['variables'][var_id] = var_value
    return run


# requests
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
    if resp is not None and (resp.status_code == 200 or resp.status_code == 201):
        return resp.json()
    elif resp.status_code != 200 and resp.status_code != 201:
        print(resp.text)
        if (resp.status_code == 400 and resp.json()[
            'message'] == 'The selected category is for individual-level runs, but no level was selected.') \
                or resp.status_code == 404:
            return resp.json()
        else:
            raise requests.exceptions.RequestException


    else:
        return None


# requests
def post_src(url, body, api_key):
    err_lim = 5
    err_cnt = 1
    request_finished = False
    resp = None
    new_headers = _h
    new_headers['X-API-Key'] = api_key
    # print(f"attempting to request from:{url}")
    # usually fails if we are requesting too quickly, even with the sleep, try 10 times fail if still not working
    # after 10
    while not request_finished and err_cnt <= err_lim:
        # print(f"attempt: {err_cnt}")
        try:
            resp = requests.post(url, headers=new_headers, json=body)
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
    if resp is not None and (resp.status_code == 200 or resp.status_code == 201):
        return resp.json()
    elif resp.status_code != 200 and resp.status_code != 201:
        print(resp.status_code)
        print(resp.text)
        raise requests.exceptions.RequestException
    else:
        return None
