import dcd.SRCHelper as srcHelper
import json
from urllib.parse import urlparse

twitch_domains = ['www.twitch.tv', 'm.twitch.tv', 'twitch.tv', 'clips.twitch.tv', 'secure.twitch.tv']
youtube_domains = ['youtube.com', 'm.youtube.com', 'youtu.be', 'www.youtube.com']
all_domains = twitch_domains + youtube_domains + ['drive.google.com', 'bilibili.com', 'www.bilibili.com']

hacks_file = open('hacks.json')

if __name__ == '__main__':
    hacks = json.load(hacks_file)
    twitch_wrs = []
    game_id = None
    game_category = None
    for hack in hacks:
        game_id = hack['id']
        for category in hack['categories']:
            game_category = hack['categories'][category]

            url = srcHelper.get_leaderboard_for_game_category(game_id, game_category)
            res = srcHelper.request_src(url)

            if 'message' in res and res['message'] == "The selected category is for individual-level runs, but no " \
                                                      "level was selected.":
                continue
            if 'runs' in res['data'] and len(res['data']['runs']) > 0:
                if 'runs' not in res['data']:
                    continue
                run = res['data']['runs'][0]['run']
                if 'videos' in run and run['videos'] is not None and 'links' in run['videos'] and run['videos'][
                    'links'] is not None and len(run['videos']['links']) > 0:
                    link = run['videos']['links'][0]['uri']
                    domain = urlparse(link).netloc
                    if domain in twitch_domains:
                        twitch_wrs.append(run)
                        print(res['data']['runs'][0])
                    elif domain not in all_domains:
                        print(f'new domain: {domain}')

    with open('wr_runs.json', 'w') as f:
        json.dump(twitch_wrs, f)
