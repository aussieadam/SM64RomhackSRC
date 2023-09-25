import datetime
import os
import time

from discord import SyncWebhook
from discord import SyncWebhookMessage

import requests
import json
import argparse
from datetime import datetime as dt, timedelta
from dotenv import load_dotenv
from table2ascii import table2ascii as t2a, PresetStyle
from googleapiclient.discovery import build
from google.oauth2 import service_account

_HEADERS = {
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'User-Agent': 'league-leaderboards/1.0',
    'Accept': '*/*',
}
_h = dict(_HEADERS)
_sleep_period = .75
_retry_sleep = 30

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly ']
SERVICE_ACCOUNT_FILE = 'credentials.json'
load_dotenv()
SPREADSHEET_ID = os.getenv('ANNIVERSARY_SPREADSHEET_ID')
WEBHOOK_URL = os.getenv('ANNIVERSARY_WEBHOOK_URL')
MY_WEBHOOK_URL = os.getenv('MY_ANNIVERSARY_WEBHOOK_URL')


def valid_date(s):
    try:
        return dt.strptime(s, "%B %d, %Y")
    except ValueError:
        msg = "not a valid date: {0!r}".format(s)
        raise argparse.ArgumentTypeError(msg)


def get_anniversaries(doc, spreadsheet_id, hack_list_range):
    today = dt.today()
    hacks_sheet = doc.get(spreadsheetId=spreadsheet_id, ranges=hack_list_range, includeGridData=True).execute()
    hacks_list = hacks_sheet['sheets'][0]['data'][0]['rowData']
    hacks = []
    for hack_data in hacks_list:
        hack = hack_data['values']
        # is an actual data row
        if hack is not None and len(hack) == 4 and 'effectiveValue' in hack[1]:
            hack_name = hack[0]['effectiveValue']['stringValue']
            hack_hyperlink = None
            if 'hyperlink' in hack[0]:
                hack_hyperlink = hack[0]['hyperlink']
            else:
                print(f"missing hyperlink for {hack_name}")
            star_count = hack[1]['effectiveValue']['stringValue']
            authors = hack[2]['effectiveValue']['stringValue']
            release_date = valid_date(hack[3]['effectiveValue']['stringValue'])
            year_diff = today.year - release_date.year
            hack_json = {'hack_name': hack_name, 'hyperlink': hack_hyperlink, 'star_count': star_count,
                         'authors': authors, 'release_date': release_date, 'year_diff': year_diff}

            if year_diff != 0 and (
                    year_diff == 3 or year_diff % 5 == 0) and today.month == release_date.month and today.day == release_date.day:
                hacks.append(hack_json)

    return hacks


def post_anniversaries(hack_list):
    webhook = SyncWebhook.from_url(WEBHOOK_URL)
    my_webhook = SyncWebhook.from_url(MY_WEBHOOK_URL)
    for hack in hack_list:
        message = f":cake: **{hack['hack_name']}** by {hack['authors']} was released on this day, {hack['year_diff']} years ago!"
        print(hack['hyperlink'])
        if hack['hyperlink'] is not None:
            message = message + f"\n{hack['hyperlink']}"
        my_message = my_webhook.send(content=message)
        message = webhook.send(content=message)
        my_message.publish()
        message.publish()


def lambda_handler(event, context):
    # if __name__ == '__main__':
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    document = service.spreadsheets()
    hack_range = "Primary Hack Release List!B3:E500"
    hacks = get_anniversaries(document, SPREADSHEET_ID, hack_range)
    post_anniversaries(hacks)
    if len(hacks) == 0:
        return {
            'statusCode': 200,
            'body': 'Run Complete no Anniversaries today'
        }
    else:
        return {
            'statusCode': 200,
            'body': 'Run Complete'
        }
