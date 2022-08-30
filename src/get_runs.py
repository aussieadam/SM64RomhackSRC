import dcd.SRCHelper as srcHelper
import json

if __name__ == '__main__':
    hacks_file = 'hacks.json'
    hacks= {}
    url = srcHelper.get_romhacks()
    while url is not None:
        res = srcHelper.request_src(url)
        for game in res['data']:
            hacks[game['names']['international']] = game['id']
        url = None
        for page in res['pagination']['links']:
            if page['rel'] == 'next':
                url = page['uri']
                rel = page['rel']
    with open(hacks_file,'w') as outfile:
        outfile.write(json.dumps(hacks,indent=4))
