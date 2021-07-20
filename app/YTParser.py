import io
import os
import re
import csv
import pickle
import psycopg2
import googleapiclient.errors
import google_auth_oauthlib.flow
import googleapiclient.discovery

api_version = "v3"
api_service_name = "youtube"
client_secrets_file = "client_secrets.json"
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
filters = ['vk','music','instagram','tiktok']

# TODO: in the future, could get the link to return to webpage, then wait for user to paste in the code. 
def get_auth_service():
    print("Getting service")
    if os.path.exists("CREDENTIALS_PICKLE_FILE"):
        with open("CREDENTIALS_PICKLE_FILE", 'rb') as f:
            credentials = pickle.load(f)
    else:
        print("getting flow")
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes, redirect_uri="urn:ietf:wg:oauth:2.0:oob:auto")
        credentials = flow.run_local_server(host='localhost',
                                            port=6969, 
                                            authorization_prompt_message='Please visit this URL: {url}', 
                                            success_message='The auth flow is complete; you may close this window.',
                                            open_browser=True)
        with open("CREDENTIALS_PICKLE_FILE", 'wb') as f:
            pickle.dump(credentials, f)
    return googleapiclient.discovery.build(api_service_name, api_version, credentials = credentials)

# returns link for user to follow
def get_auth_service_link():
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes, redirect_uri="urn:ietf:wg:oauth:2.0:oob")
    url = flow.authorization_url()
    return url,flow 

def get_credentials(flow,code):
    flow.fetch_token(code=code)
    credentials = flow.credentials
    return credentials 


def get_latest_video_description(channel_id):
    youtube = get_auth_service()

    response = youtube.channels().list(
        part="snippet,contentDetails",
        id=channel_id
    ).execute()

    # get "uploads" playlist ID
    channel = response['items'][0]
    contentDetails = channel['contentDetails']
    relatedPlaylists = contentDetails['relatedPlaylists']
    uploads = relatedPlaylists['uploads']
    
    playlist = youtube.playlistItems().list(
        part="snippet,contentDetails",
        maxResults=1,
        playlistId=uploads
    ).execute()

    videos = playlist['items']
    latest_video = videos[0]
    latest_video_description = latest_video['snippet']['description']
    return latest_video_description

# command defines how to extract information
def get_latest_video_description(cur,command):
    cur.execute(command) 
    rows = cur.fetchall()
    links = []
    i = 0
    for row in rows:
        try:
            channel_id = row[1]
            description = get_latest_video_description(channel_id)
            links = get_links(description)
            filtered_links = filter_links(links)
            links += filtered_links
            i += 1
            print(i)

            if i > 5:
                return links
        except:
            print(row[0])
    return links
        
def get_links(description):
    return re.findall("(?P<url>https?://[^\s]+)", description)

def filter_links(links):
    return [link for link in links if not re.search("|".join(["("+f+")" for f in filters]),link)]

def parse(filename):
    opened_file = open(filename, encoding="UTF-8")
    reader = csv.reader(opened_file)

    for row in reader: 
        try:
            channel_id = row[2]
            description = get_latest_video_description(channel_id)
            links = get_links(description)
            filtered_links = filter_links(links)
            print(filtered_links)
        except:
            print(reader.line_num)

def parse_save(contents,cursor,command):
    bytes_io = io.BytesIO(contents)
    opened_file = io.TextIOWrapper(bytes_io,encoding="UTF-8")
    reader = csv.reader(opened_file)

    ans = False
    for row in reader: 
        try:
            channel_name = row[0]
            channel_id = row[2]
            ans = True
            cursor.execute(command,(channel_name,channel_id))
        except:
            print("failed at: ", reader.line_num)
    return ans

def parse_test(filename):
    opened_file = open(filename, encoding="UTF-8")
    reader = csv.reader(opened_file)

    ans = ""
    for row in reader: 
        ans += row
    return ans

# def parse():
#     opened_file = open('input.csv', encoding="UTF-8")
#     reader = csv.reader(opened_file)

#     for row in reader: 
#         try:
#             channel_id = row[2]
#             description = get_latest_video_description(channel_id)
#             links = get_links(description)
#             filtered_links = filter_links(links)
#             print(filtered_links)
#         except:
#             print(reader.line_num)