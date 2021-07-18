import os
import re
import csv
import pickle
import googleapiclient.errors
import google_auth_oauthlib.flow
import googleapiclient.discovery

api_version = "v3"
api_service_name = "youtube"
client_secrets_file = "client_secrets.json"
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
filters = ['vk','music','instagram','tiktok']

def get_auth_service():
    if os.path.exists("CREDENTIALS_PICKLE_FILE"):
        with open("CREDENTIALS_PICKLE_FILE", 'rb') as f:
            credentials = pickle.load(f)
    else:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
        credentials = flow.run_console()
        with open("CREDENTIALS_PICKLE_FILE", 'wb') as f:
            pickle.dump(credentials, f)
    return googleapiclient.discovery.build(api_service_name, api_version, credentials = credentials)

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