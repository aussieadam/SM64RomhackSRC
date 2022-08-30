import dcd.SRCHelper as srcHelper
import json
import argparse
import datetime
from datetime import datetime as dt
from datetime import timedelta


def valid_date(s):
    try:
        return dt.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        msg = "not a valid date: {0!r}".format(s)
        raise argparse.ArgumentTypeError(msg)


# Args
parser = argparse.ArgumentParser(description="NBA Stats, Game/PlaybyPlay pull")

parser.add_argument('-g', '--game', required=False, type=str, default='SM64 Sapphire',
                    help='game to get runs from')
parser.add_argument('-lrd', '--last_ran_date', required=False, type=valid_date, default='2022-01-01T12:00:00Z',
                    help='last time this was ran to fetch latest runs')
parser.add_argument('-c', '--category', required=False, type=str, default='30 Star',
                    help='category of hack')
args = parser.parse_args()

last_ran_date = args.last_ran_date
game = args.game
category = args.category
hacks_file = open('hacks.json')

if __name__ == '__main__':
    hacks = json.load(hacks_file)
    game_id = None
    game_category = None
    for hack in hacks:
        if hack['name'] == game or hack['id'] == game:
            game_id = hack['id']
            game_category = hack['categories'][category]

    url = srcHelper.get_runs_for_game_category(game_id, game_category)
    while url is not None:
        res = srcHelper.request_src(url)
        print(json.dumps(res, indent=4, sort_keys=True))
        for run in res['data']:
            # get date of verified so we can compare if we've already seen this run
            verified_date = dt.strptime(run['status']['verify-date'], '%Y-%m-%dT%H:%M:%SZ')
            if verified_date > last_ran_date:
                print(verified_date)
            else:
                url = None
        # if the last run of page isn't before the last time this ran, keep paginating
        if url is not None:
            url = None
            for page in res['pagination']['links']:
                if page['rel'] == 'next':
                    url = page['uri']
