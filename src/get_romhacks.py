import dcd.SRCHelper as srcHelper
import json
import time

start_time = time.time()

if __name__ == '__main__':
    # this will write to local directory you are currently in, up to you to change it
    hacks_file = 'hacks.json'
    hacks = []
    url = srcHelper.get_romhacks()
    while url is not None:
        res = srcHelper.request_src(url)
        # print(json.dumps(res, indent=4))
        for game in res['data']:
            # print(json.dumps(game, indent=4))
            # moderator check to make sure we are all on every game
            if 'v8lyv4jm' not in game['moderators']:
                print(f"{game['abbreviation']} is missing MarvJungs")
            if 'qxkrpqm8' not in game['moderators']:
                print(f"{game['abbreviation']} is missing Dackage")
            if 'pj0n70m8' not in game['moderators']:
                print(f"{game['abbreviation']} is missing FrostyZako")
            if 'qjopronx' not in game['moderators']:
                print(f"{game['abbreviation']} is missing Tomatobird8")
            if 'zxzlkr08' not in game['moderators']:
                print(f"{game['abbreviation']} is missing AndrewSM64")
            if 'v8lk144x' not in game['moderators']:
                print(f"{game['abbreviation']} is missing Phanton")
            if '68wzrnv8' not in game['moderators']:
                print(f"{game['abbreviation']} is missing aussieadam")
            if 'kj957778' not in game['moderators']:
                print(f"{game['abbreviation']} is missing DJ_Tala")
            game_json = {'name': game['names']['international'], 'id': game['id'], 'abbreviation': game['abbreviation']}
            levels = game['levels']['data']
            level_json = {}
            for lev in levels:
                level_json[lev['id']] = lev['name']
            cat_res = game['categories']
            categories_json = {}
            for category in cat_res['data']:
                categories_json[category['name']] = category['id']
            game_json['categories'] = categories_json
            variables_res = game['variables']
            variables_json = {}
            for variable in variables_res['data']:
                if variable['scope'] is not None and variable['scope']['type'] == 'single-level':
                    variables_json[level_json[variable['scope']['level']]] = variable['values']
                    variables_json[level_json[variable['scope']['level']]]['id'] = variable['id']
                    variables_json[level_json[variable['scope']['level']]]['level_id'] = variable['scope']['level']
                    variables_json[level_json[variable['scope']['level']]]['var_name'] = variable['name']
                else:
                    variables_json[variable['name']] = variable['values']
                    variables_json[variable['name']]['id'] = variable['id']
            game_json['variables'] = variables_json
            hacks.append(game_json)
        url = None
        for page in res['pagination']['links']:
            if page['rel'] == 'next':
                url = page['uri']
    with open(hacks_file, 'w') as outfile:
        outfile.write(json.dumps(hacks, indent=4))

    print(f"---Finished in {(time.time() - start_time)} seconds ---")

