import os

from discord import SyncWebhook,Embed
from dotenv import load_dotenv
import requests
import time
import json
from datetime import datetime as dt, timedelta as td

# stole these from firefox, default headers were redirecting too many times
_HEADERS = {
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'User-Agent': 'romhack-wrs/1.0',
    'Accept': '*/*',
}
_h = dict(_HEADERS)
_sleep_period = .60
_retry_sleep = 30
start_time = dt.today()

load_dotenv()
MY_WEBHOOK_URL = os.getenv('MY_WEBHOOK_URL')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

wrs = []


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

def post_runs():
    if wrs:
        webhook = SyncWebhook.from_url(WEBHOOK_URL)
        my_webhook = SyncWebhook.from_url(MY_WEBHOOK_URL)
        embeds = []
        webhook.send("Congratulations to the following runners for Fullgame WR's in the last week:")
        my_webhook.send("Congratulations to the following runners for Fullgame WR's in the last week:")
        for wr in wrs:
            embed = Embed(title=f"{wr['game']} : {wr['category']} in {wr['time']}",url=wr['run_link'])
            embed.add_field(name="Player",value=wr['player'],inline=False)
            if "image" in wr and wr['image'] is not None:
                embed.set_thumbnail(url=wr['image'])
            if "youtube_link" in wr and wr['youtube_link'] is not None:
                embed.add_field(name="Youtube",value=f"[{wr['player']} Youtube]({wr['youtube_link']})",inline=True)
            if "twitch_link" in wr and wr['twitch_link'] is not None:
                embed.add_field(name="Twitch", value=f"[{wr['player']} Twitch]({wr['twitch_link']})", inline=True)
            if "twitter_link" in wr and wr['twitter_link'] is not None:
                embed.add_field(name="Twitter", value=f"[{wr['player']} Twitter]({wr['twitter_link']})", inline=True)
            embeds.append(embed)
            if len(embeds) == 10:
                webhook.send(embeds=embeds)
                my_webhook.send(embeds=embeds)
                embeds = []
        if len(embeds) >0:
            webhook.send(embeds=embeds)
            my_webhook.send(embeds=embeds)

def lambda_handler(event, context):
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
                            wr_json['twitter_link'] = user_res['twitter']['uri']
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

    post_runs()
    return {
        'statusCode': 200,
        'body': 'Run Complete'
    }

# if __name__ == "__main__":
   # lambda_handler(1,1)