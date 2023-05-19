import dcd.SRCHelper as srcHelper
import json
from datetime import datetime as dt, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt



def get_new_runs(since_date, to_date):
    hacks = json.load(open('hacks.json'))
    runs = []
    for hack in hacks:
        url = srcHelper.get_runs_for_game(hack['id'])
        while url is not None:
            res = srcHelper.request_src(url)
            # print(url)
            for run in res['data']:
                current_run = {}
                # get date of verified so we can compare if we've already seen this run
                verified_date = run['status']['verify-date']
                if verified_date is not None and dt.strptime(verified_date,
                                                             '%Y-%m-%dT%H:%M:%SZ') > dt.strptime(to_date,
                                                                                                 '%Y-%m-%dT%H:%M:%SZ'):
                    continue
                elif verified_date is not None and dt.strptime(verified_date,
                                                               '%Y-%m-%dT%H:%M:%SZ') >= dt.strptime(since_date,
                                                                                                    '%Y-%m-%dT%H:%M:%SZ'):
                    runs.append({"Game": hack['name'], "Run_Time": run['times']['primary_t'],
                                 "Examiner": run['status']['examiner']})
                else:
                    url = None
                    break
            # if the last run of page isn't before the last time this ran, keep paginating
            if url is not None:
                url = None
                for page in res['pagination']['links']:
                    if page['rel'] == 'next':
                        url = page['uri']
    return runs

def get_examiner_names():
    runs = json.load(open('last_years_runs.json'))
    print(runs)
    mods = {}
    for run in runs:
        mod = run['Examiner']
        if mod not in mods:
            url = srcHelper.get_user(mod)
            res = srcHelper.request_src(url)['data']
            mods[mod] = res["names"]['international']
    print(mods)

if __name__ == '__main__':


    since_date = '2023-01-01T00:00:00Z'
    to_date = '2024-01-01T00:00:00Z'
    runs = get_new_runs(since_date, to_date)
    with open("last_years_runs.json", 'w') as outfile:
        outfile.write(json.dumps(runs, indent=4))

    runs = json.load(open('last_years_runs.json'))
    df2 = pd.DataFrame(runs)
    examiner_df = df2.groupby(["Examiner"])['Examiner'].count().sort_values(ascending=False)
    game_df = df2.groupby(["Game"])['Game'].count().sort_values(ascending=False)
    print(examiner_df)
    print(game_df.to_string())
    examiner_df.plot.pie(subplots=True, figsize=(8, 3))
    plt.show()
    game_df.plot.bar(subplots=True, figsize=(8, 3))
    plt.show()

