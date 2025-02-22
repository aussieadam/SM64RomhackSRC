import dcd.SRCHelper as srcHelper
import json
from urllib.parse import urlparse


runs_file = open('wr_runs.json')
SRC_API_KEY = os.getenv('SRC_API_KEY')

if __name__ == '__main__':
    runs = json.load(runs_file)
    for run in runs:
        user_id = run['players'][0]['id']
        game_id = run['game']
        run_id = run['id']
        category_id = run['category']
        video_link = run['uploaded-to']
        run_time = run['primary_t']
        emulated = run['system']['emulated']
        platform_id = run['system']['platform']
        run_date = run['date']
        if user_id not in ['68wzrnv8'] or video_link == 'does not exist':
            continue
        print(run)
        delete_url = srcHelper.delete_run(run_id)
        add_run_body = srcHelper.get_fullgame_run_body(user_id,run_time,run_date,platform_id,emulated,video_link,category_id)
        runs_url = srcHelper.get_runs_url()
        post_src_res = srcHelper.post_src(runs_url, add_run_body, SRC_API_KEY)