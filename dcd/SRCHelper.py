import time

import requests

# stole these from firefox, default headers were redirecting too many times
_HEADERS = {
    'Host': 'www.speedrun.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0',
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


# url help
def get_runs_for_game_category(game_id, category):
    return f'https://www.speedrun.com/api/v1/runs?game={game_id}&category={category}&status=verified&orderby=verify-date&direction=desc&embed=players'


def get_leaderboard_for_game_category(game_id, category):
    return f'https://www.speedrun.com/api/v1/leaderboards/{game_id}/category/{category}?embed=players'


def get_runs_for_game(game_id):
    return f'https://www.speedrun.com/api/v1/runs?game={game_id}&status=verified&orderby=verify-date&direction=desc'


def get_romhacks():
    return f'https://www.speedrun.com/api/v1/series/0499o64v/games?max=200&embed=categories'


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
            print(f"Error Getting Response from {url}" )
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
