import requests
import time
from datetime import datetime as dt, timedelta as td

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
start_time = dt.today()



def request_src(request_url):
    err_lim = 5
    err_cnt = 1
    request_finished = False
    resp = None
    # print(f"attempting to request from:{request_url}")
    # usually fails if we are requesting too quickly, even with the sleep, try 10 times fail if still not working
    # after 10
    while not request_finished and err_cnt <= err_lim:
        # print(f"attempt: {err_cnt}")
        try:
            resp = requests.get(request_url, headers=_h)
            request_finished = True
            # print("request finished")
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            print(f"Error Getting Response from {request_url}")
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


if __name__ == '__main__':
    job_start_time = time.time()
    wrs = []
    # hacks string
    url = f'https://www.speedrun.com/api/v1/series/0499o64v/games?max=200&embed=categories'
    while url is not None:
        res = request_src(url)
        for game in res['data']:
            game_name = game['names']['international']
            game_id = game['id']
            cat_res = game['categories']['data']

            try:
                game_url = f"https://www.speedrun.com/api/v1/games/{game_id}/records?scope=full-game&top=1&embed=players"
                wr_results = request_src(game_url)['data']
            except requests.exceptions.RequestException as err:
                print(
                    f"Not a proper category or no runs submitted for: {game_name}: , error in wr url: {game_url}, error message: {err}")
                continue

            for wr_res in wr_results:
                wr_json = {'game': game_name}
                if wr_res['runs'] and wr_res['runs'][0]['run']['status'][
                    'verify-date'] is not None:
                    wr_run = wr_res['runs'][0]['run']
                    for cat in cat_res:
                        if cat['id'] == wr_run['category']:
                            wr_json['category'] = cat['name']
                            break
                    verified_date = dt.strptime(wr_run['status']['verify-date'], '%Y-%m-%dT%H:%M:%SZ')
                    if verified_date >= start_time - td(days=7):
                        user_url = wr_run['players'][0]['uri']
                        user_res = wr_res['players']['data'][0]
                        wr_json['run_link'] = wr_run['weblink']
                        wr_time_string = str(td(seconds=wr_run['times']['primary_t']))
                        if len(wr_time_string) > 3 and wr_time_string[-3:] == '000':
                            wr_time_string = wr_time_string[:-3]
                        if len(wr_time_string) > 2 and wr_time_string[0:2] == '0:':
                            wr_time_string = wr_time_string[2:]
                        wr_json['time'] = wr_time_string
                        wr_json['player'] = user_res['names']['international']
                        if user_res['youtube']:
                            wr_json['youtube_link'] = user_res['youtube']['uri']
                        if user_res['twitch']:
                            wr_json['twitch_link'] = user_res['twitch']['uri']
                        if user_res['twitter']:
                            wr_json['twitter_link'] = user_res['twitch']['uri']
                        if user_res['assets']:
                            if user_res['assets']['image']['uri'] is not None:
                                wr_json['image'] = user_res['assets']['image']['uri']
                            elif user_res['assets']['icon']['uri'] is not None:
                                wr_json['image'] = user_res['assets']['icon']['uri']

                        wrs.append(wr_json)
        url = None
        for page in res['pagination']['links']:
            if page['rel'] == 'next':
                url = page['uri']

    if wrs:
        message = "Congratulations to the following runners for Fullgame WR's in the last week:"
        for wr in wrs:
            message = message + f"\n {wr['player']} With a time of {wr['time']} in: {wr['game']} : {wr['category']}"
        print(message)

    print(f"---{time.time() - job_start_time} seconds ---")