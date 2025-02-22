import dcd.SRCHelper as srcHelper
import json
import argparse
import datetime
from datetime import datetime as dt
from datetime import timedelta
from urllib.parse import urlparse

twitch_domains = ['m.twitch.tv','go.twitch.tv','secure.twitch.tv','twitch.tv','www.twitch.tv','clips.twitch.tv']
all_domains = twitch_domains + ['twitter.com','www.bilibili.com','www.nicovideo.jp','plus.google.com','vimeo.com', 'imgur.com', 'streamable.com', 'cdn.discordapp.com',
 'i.imgur.com', 'm.youtube.com', 'drive.google.com', 'www.youtube.com', 'youtu.be', 'youtube.com']
hacks_file = open('hacks.json')

if __name__ == '__main__':
    hacks = json.load(hacks_file)
    game_id = None
    twitch_count = 0
    run_time = 0
    game_count ={}
    for hack in hacks:
        game_twitch_count = 0
        game_time = 0
        game_id = hack['id']
        game_name = hack['name']

        url = srcHelper.get_runs_for_game(game_id)
        while url is not None:
            res = srcHelper.request_src(url)
            for run in res['data']:
                if run['videos'] is not None and 'links' in run['videos'] :
                    link = run['videos']['links'][0]['uri']
                    domain = urlparse(link).netloc
                    if domain not in all_domains:
                        print(f"new domain {domain}")
                    if domain in twitch_domains:
                        twitch_count = twitch_count+1
                        game_twitch_count = game_twitch_count +1
                        game_time = game_time + run['times']['primary_t']
                        run_time = run_time + run['times']['primary_t']

            # if the last run of page isn't before the last time this ran, keep paginating
            if url is not None:
                url = None
                for page in res['pagination']['links']:
                    if page['rel'] == 'next':
                        url = page['uri']
        if game_twitch_count > 0:
            game_count[game_name] = game_twitch_count
            print(f"{game_name} has {game_twitch_count} twitch runs for a total of {game_time} seconds")
    print(game_count)
    print(twitch_count)
    print(run_time)
    print(f"{len(game_count)} games have {twitch_count} runs on twitch, totalling {round(run_time,0)} seconds ({str(datetime.timedelta(seconds=run_time))})")
