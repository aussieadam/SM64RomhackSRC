import dcd.SRCHelper as srcHelper
import json
from urllib.parse import urlparse

twitch_problem_domains = ['www.twitch.tv', 'm.twitch.tv', 'twitch.tv', 'secure.twitch.tv']
youtube_domains = ['youtube.com', 'm.youtube.com', 'youtu.be', 'www.youtube.com']
all_domains = twitch_problem_domains + youtube_domains + ['drive.google.com', 'bilibili.com', 'www.bilibili.com','clips.twitch.tv','streamable.com']


hacks_file = open('hacks.json')
wrs_file = 'wr_runs.json'

if __name__ == '__main__':
    new_twitch_wrs = []
    twitch_wrs = []
    with open(wrs_file) as json_data:
        twitch_wrs = json.load(json_data)
    hacks = json.load(hacks_file)
    game_id = None
    game_category = None
    matched_ids = []
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
                if 'videos' in run and run['videos'] is not None:
                    twitch_found = False
                    youtube_found = False
                    for link in run['videos']['links']:
                        link_uri = link['uri']
                        domain = urlparse(link_uri).netloc
                        if domain in youtube_domains:
                            youtube_found = True
                        if domain in twitch_problem_domains:
                            twitch_found = True
                        if domain not in all_domains:
                            print(f'new domain: {domain}')
                    wr_exists_already = False
                    if twitch_found and not youtube_found:
                        matched_ids.append(run['id'])
                        for wr in twitch_wrs:
                            if wr['id'] == run['id']:
                                wr_exists_already = True
                        if not wr_exists_already:
                            new_twitch_wrs.append(run)

                            print(res['data']['runs'][0])

    with open(wrs_file) as json_data:
        for wr in json.load(json_data):
            if wr['id'] in matched_ids:
                new_twitch_wrs.append(wr)

    with open(wrs_file, 'w') as f:
        json.dump(new_twitch_wrs, f)
