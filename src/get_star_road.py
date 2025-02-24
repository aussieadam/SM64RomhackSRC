from datetime import datetime as dt

import dcd.SRCHelper as srcHelper

url = 'https://www.speedrun.com/api/v1/runs?game=j1np0w6p&category=zd35lrkn&max=200&status=verified&orderby=verify-date&direction=desc'

triforce_date = '2019-10-03'
chris_date = '2022-06-12'
chris_runs = []
triforce_runs = []
while url is not None:
    res = srcHelper.request_src(url)

    # print(url)
    for run in res['data']:
        print(run)
        current_run = {}
        # get date of verified so we can compare if we've already seen this run
        verified_date = run['status']['verify-date']
        if verified_date is not None and dt.strptime(verified_date,
                                                     '%Y-%m-%dT%H:%M:%SZ') >= dt.strptime(chris_date,
                                                                                         '%Y-%m-%d'):
            chris_runs.append(run)

        elif verified_date is not None and dt.strptime(verified_date,
                                                       '%Y-%m-%dT%H:%M:%SZ') < dt.strptime(chris_date,
                                                                                            '%Y-%m-%d') and dt.strptime(verified_date,
                                                     '%Y-%m-%dT%H:%M:%SZ') >= dt.strptime(triforce_date,
                                                                                         '%Y-%m-%d'):
            triforce_runs.append(run)
    # if the last run of page isn't before the last time this ran, keep paginating
    if url is not None:
        url = None
        for page in res['pagination']['links']:
            if page['rel'] == 'next':
                url = page['uri']


print(len(triforce_runs))
print(len(chris_runs))