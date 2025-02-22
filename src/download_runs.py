import json
import yt_dlp

import os
import google_auth_oauthlib
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = 'token.json'
wrs_file = 'wr_runs.json'


def authenticate_youtube():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)

    # Load client secrets file, put the path of your file
    client_secrets_file = "client_secret_256224785504-rj2to7oheoudsf6trui2m1h93ncvfe2e.apps.googleusercontent.com.json"

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, SCOPES)
    credentials = flow.run_local_server()

    youtube = googleapiclient.discovery.build(
        "youtube", "v3", credentials=credentials)

    return youtube



def upload_video(youtube,run, video):
    request_body = {
        "snippet": {
            "categoryId": "22",
            "title": video[7:],
            "description": f"Uploaded from AussieAdam Python Script: {str(run)}",
            "tags": ["test", "python", "api"]
        },
        "status": {
            "privacyStatus": "unlisted"
        }
    }

    # put the path of the video that you want to upload
    media_file = video

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=googleapiclient.http.MediaFileUpload(media_file, chunksize=-1, resumable=True)
    )

    response = None

    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload {int(status.progress() * 100)}%")

        print(f"Video uploaded with ID: {response['id']}")
        return response


def download_video(run):
    ydl_options = {
        'format': 'worstvideo*',
        'outtmpl': 'videos/%(title)s.%(ext)s',
        'noplaylist': True,
        'concurrent_fragment_downloads': 10,
        'verbose': True,  # for debugging stuff
        'sleep-interval': 5,  # so i dont get insta blacklisted by twitch
        'retries': 1,  # Retry a second time a bit later in case there was simply an issue
        'retry-delay': 10,  # Wait 10 seconds before retrying
    }

    run_url = run['videos']['links'][0]['uri']
    with yt_dlp.YoutubeDL(ydl_options) as ydl:
        try:
            file_name = ydl.extract_info(run_url,download=True)['requested_downloads'][0]['_filename']
            print(file_name)
            ydl.close()
            return file_name

        except yt_dlp.utils.DownloadError as e:
            print(f"Skipping invalid or dead link: {run_url} - Error: {e}")
            return
        except yt_dlp.utils.ExtractorError as e:
            # In case you get rate limited. I did. It automatically goes through all downloads in this case and
            # removes the urls unfairly.
            if "HTTP Error 403: Forbidden" in str(e):
                print(f"Error: {e}")
                print("There is a rate limit or some other access restriction (403 Forbidden).")
                return  # Exit the function and resume later


if __name__ == "__main__":
    youtube = authenticate_youtube()
    print(youtube)
    with open(wrs_file) as json_data:
        d = json.load(json_data)

    i = 0
    for row in d:
        print(f'iteration {i} of {len(d)}')
        if 'uploaded-to' in row:
            i = i+1
            continue
        print(row)
        #skip long files (above 10 hours), youtube can't process
        if row['times']['primary_t'] >= 36000:
            file = None
            print('file too long, skipping download')
        else:
            file = download_video(row)
            print('download complete')
        res = None
        if file is not None:
            print('begin upload')
            res = upload_video(youtube, row, file)
            d[i]['uploaded-to'] = f"youtube.com/{res['id']}"
            os.remove(file)
        else:
            d[i]['uploaded-to'] = 'does not exist'

        with open(wrs_file, 'w') as f:
            json.dump(d, f)
        i = i + 1
