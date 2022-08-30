import dcd.SRCHelper as srcHelper
import json

if __name__ == '__main__':
    hacks_file = 'hacks.json'
    hacks= []
    url = srcHelper.get_romhacks()
    while url is not None:
        res = srcHelper.request_src(url)
        for game in res['data']:
            game_json = {'name': game['names']['international'], 'id': game['id'], 'abbreviation': game['abbreviation']}
            for link in game['links']:
                if link['rel']=='categories':
                    cat_res = srcHelper.request_src(link['uri'])
                    categories_json = {}
                    for category in cat_res['data']:
                        categories_json[category['name']] = category['id']
                    game_json['categories'] = categories_json
            hacks.append(game_json)
        url = None
        for page in res['pagination']['links']:
            if page['rel'] == 'next':
                url = page['uri']
    with open(hacks_file,'w') as outfile:
        outfile.write(json.dumps(hacks,indent=4))