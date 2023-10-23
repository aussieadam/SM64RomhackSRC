import dcd.SRCHelper as srcHelper
import json
import time

start_time = time.time()

if __name__ == '__main__':
    # this will write to local directory you are currently in, up to you to change it
    irl_games_file = 'irl_games.json'
    irl_games = []
    url = srcHelper.get_games_and_categories()
    while url is not None:
        res = srcHelper.request_src(url)
        # print(json.dumps(res, indent=4))
        for game in res['data']:
            game_json = {'name': game['names']['international'], 'id': game['id'], 'abbreviation': game['abbreviation']}
            cat_res = game['categories']
            categories_json = {}
            has_cat = False
            for category in cat_res['data']:
                cat_name = category['name']
                rules = category['rules']
                if (cat_name is not None and (
                        ('irl' in cat_name.lower() and 'girl' not in cat_name.lower() and 'twirl' not in cat_name.lower() and 'whirl' not in cat_name.lower())
                        or 'in real life' in cat_name.lower())) \
                        or (rules is not None and (('in real life' in rules.lower()) or (
                        'IRL' in rules and 'GIRL' not in rules and 'TWIRL' not in rules and 'WHIRL' not in rules))):
                    game_json['category'] = category
                    has_cat = True
            if has_cat:
                #print(game_json)
                irl_games.append(game_json)
        url = None
        for page in res['pagination']['links']:
            if page['rel'] == 'next':
                url = page['uri']
    with open(irl_games_file, 'w') as outfile:
        outfile.write(json.dumps(irl_games, indent=4))

    print(f"---Finished in {(time.time() - start_time)} seconds ---")
