import dcd.SRCHelper as srcHelper
import json

if __name__ == '__main__':
    hacks_file = 'hacks.json'
    hacks = []
    url = srcHelper.get_romhacks()
    while url is not None:
        res = srcHelper.request_src(url)
        # print(json.dumps(res, indent=4))
        for game in res['data']:
            # print(json.dumps(game, indent=4))
            if 'v8lyv4jm' not in game['moderators']:
                print(f"{game['abbreviation']} is missing MarvJungs")
            if '18v52d5j' not in game['moderators']:
                print(f"{game['abbreviation']} is missing Spaceman")
            if 'pj0n70m8' not in game['moderators']:
                print(f"{game['abbreviation']} is missing FrostyZako")
            if 'qjopronx' not in game['moderators']:
                print(f"{game['abbreviation']} is missing Tomatobird8")
            if 'qxkm6d2j' not in game['moderators']:
                print(f"{game['abbreviation']} is missing sizzlingmario4")
            if 'zxzlkr08' not in game['moderators']:
                print(f"{game['abbreviation']} is missing AndrewSM64")
            if 'v8lk144x' not in game['moderators']:
                print(f"{game['abbreviation']} is missing Phanton")
            if '68wzrnv8' not in game['moderators']:
                print(f"{game['abbreviation']} is missing aussieadam")
            game_json = {'name': game['names']['international'], 'id': game['id'], 'abbreviation': game['abbreviation']}
            cat_res = game['categories']
            categories_json = {}
            for category in cat_res['data']:
                categories_json[category['name']] = category['id']
            game_json['categories'] = categories_json
            hacks.append(game_json)
        url = None
        for page in res['pagination']['links']:
            if page['rel'] == 'next':
                url = page['uri']
    with open(hacks_file, 'w') as outfile:
        outfile.write(json.dumps(hacks, indent=4))
