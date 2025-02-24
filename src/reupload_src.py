import dcd.SRCHelper as srcHelper
import json
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

SRC_API_KEY = os.getenv('SRC_API_KEY')
runs_file = 'wr_runs.json'
reject_body = {"status": {"status": "rejected",
                          "reason": "this is a WR twitch vod, needs to be a youtube vod, feel free to reupload to "
                                    "youtube."}
               }

if __name__ == '__main__':
    runs = None
    with open(runs_file) as json_data:
        runs = json.load(json_data)
    i = -1
    for run in runs:
        i = i + 1
        user_id = run['players'][0]['id']
        game_id = run['game']
        run_id = run['id']
        category_id = run['category']
        video_link = run['uploaded-to']
        run_time = run['times']['primary_t']
        emulated = run['system']['emulated']
        platform_id = run['system']['platform']
        run_date = run['date']
        #skip runs by these people, and ones we have already reuploaded
        if user_id not in ['68wzrnv8'] or video_link == 'does not exist' or 'reupload-status' in run:
            continue
        print(run)
        unverify_url = srcHelper.unverify_run(run_id)
        print(unverify_url)
        unverify_res = srcHelper.put_src(unverify_url, reject_body, SRC_API_KEY)
        print(unverify_res)
        add_run_body = srcHelper.get_fullgame_run_body(user_id, run_time, run_date, platform_id, emulated, video_link,category_id)
        runs_url = srcHelper.get_runs_url()
        post_src_res = srcHelper.post_src(runs_url, add_run_body, SRC_API_KEY)
        print(post_src_res)
        runs[i]['reupload-status'] = True
        with open(runs_file,'w') as f:
            json.dump(runs,f)