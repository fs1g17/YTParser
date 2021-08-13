import io
import os
import re
import csv
import pickle
import psycopg2
from models import *
from fastapi import Depends
from database import get_db
import googleapiclient.errors
from datetime import datetime 
import google_auth_oauthlib.flow
import googleapiclient.discovery
from sqlalchemy.orm import Session

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


#-------------------------------- PARSE FUNCTIONS -------------------------------------
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

#asaync or not??
def get_links_from_rows(rows):
    links = []
    for row in rows:
        try:
            channel_id = row[1]
            description = get_latest_video_description(channel_id)
            links = get_links(description)
            filtered_links = filter_links(links)
            links += filtered_links
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

#--------------------------------CHANNEL FUNCTIONS -----------------------------------
def get_uploads(channel_id,youtube):
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
        maxResults=50,
        playlistId=uploads
    ).execute()

    #videos = playlist['items']
    return playlist

def get_uploads_next_page(channel_id,next_page_token,youtube):
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
        maxResults=50,
        playlistId=uploads,
        pageToken=next_page_token
    ).execute()

    return playlist

#---------------------------- VIDEO FUNCTIONS -------------------------
def get_date(video):
    content_details = video['contentDetails']
    date = content_details['videoPublishedAt']
    return date 

def get_title(video):
    snippet = video['snippet']
    title = snippet['title']
    return title

def get_description(video):
    snippet = video['snippet']
    description = snippet['description']
    return description

def get_views(video,youtube):
    video_id = video['contentDetails']['videoId']

    ans = youtube.videos().list(
        part="statistics",
        id=video_id
    ).execute()

    items = ans['items'][0]
    stats = items['statistics']
    views = stats['viewCount']
    return views

def get_link(video):
    snippet = video['snippet']
    resource = snippet['resourceId']
    video_id = resource['videoId']
    base_url = "https://www.youtube.com/watch?v="
    return base_url + video_id

def get_video_id(video):
    snippet = video['snippet']
    resource = snippet['resourceId']
    video_id = resource['videoId']
    return video_id

#------------------------------- PARSE FUNCTIONS --------------------------
def parse_date(date:str):
    date = datetime.strptime(date,'%Y-%m-%dT%H:%M:%SZ')
    return date

# need to make sure the numbers are in range!!
# month can't be more than 12, day can't be more than #days in month!
def change_date(date:str, year:int, month:int, day:int = 0):
    date = parse_date(date)
    new_year = date.year + year
    new_month = date.month + month
    new_day = date.day + day
    date = date.replace(year=new_year,month=new_month,day=new_day)
    return date 

def get_videos_by_date_change(youtube: googleapiclient.discovery.Resource, channel_id: str, start_date:datetime, year:int, month:int, day:int=0):
    start = datetime.strftime(start_date,'%Y-%m-%dT%H:%M:%SZ')
    end_date = change_date(start,year,month,day)

    playlist = get_uploads(channel_id,youtube)

    next_page_token = ""
    if 'nextPageToken' in playlist:
        next_page_token = playlist['nextPageToken']
    videos = playlist['items']
    
    curr_date = parse_date(get_date(videos[0]))
    all_videos = []
    while(curr_date >= end_date):
        for video in videos:
            if curr_date > start_date:
                continue
            curr_date = parse_date(get_date(video))

            if curr_date < end_date:
                break
            all_videos.append(video)

        if not(next_page_token == ""):
            playlist = get_uploads_next_page(channel_id,next_page_token,youtube)
            if 'nextPageToken' in playlist:
                next_page_token = playlist['nextPageToken']
            else:
                next_page_token = ""
            videos = playlist['items']
        else:
            break 
    return all_videos

def search_by_keyword_last_year(channel_name: str, channel_id: str, word: str):
    youtube = get_auth_service()

    date_now = datetime.now()
    word = word.lower()
    year_videos = get_videos_by_date_change(youtube,channel_id,date_now,-1,0,0)

    keyword_search = []
    for video in year_videos:
        description = get_description(video).lower()
        if word in description:
            views = get_views(video,youtube)
            date = get_date(video)
            link = get_link(video)
            keyword_search.append((word,channel_name,date,views,link))

    return keyword_search

# Saving snippet info to PostgreSQL db for a creator 
def cache_to_db(db,channel_name):
    results = db.execute("SELECT * FROM creators WHERE channel_name='" + channel_name + "';")
    channel_id = ""
    for row in results:
        channel_id = row[1]

    # TODO: check what the latest video date for a creator is
    youtube = get_auth_service()
    start_date = datetime.now()
    year_videos = get_videos_by_date_change(youtube,channel_id,start_date,-1,0,0)

    # save all videos from the past year
    for video in year_videos:
        video_date = get_date(video)
        video_view = get_views(video,youtube)
        video_desc = get_description(video)
        video_info = {"date":video_date,"views":video_view,"description":video_desc}
        infostring = str(video_info).replace("'","\"")
        video_id = get_video_id(video)

        # if video is already cached, skip 
        if db.execute("SELECT * FROM videos WHERE channel_id='%s' AND video_id='%s'"%(channel_id,video_id)).rowcount > 0:
            continue 

        to_add = Video(
            channel_id = str(channel_id),
            video_id = str(video_id),
            video_info = str(video_info)
        )
        db.add(to_add)
    return True

# to parse video_info as a dict, we need to replace \' with \" and vice versa
def clean_description(video_info: str):
    output = ""
    for letter in video_info:
        if letter == '\'':
            output += '\"'
            continue

        if letter == '\"':
            output += '\''
            continue

        output += letter 

    output = output.replace("\\n","")
    output = output.replace("\n","")
    return output


#--------------------------- GUI functions -----------------------------
def get_video_id_from_video_url(video_url: str):
    info = video_url.split("youtube.com/watch?v=")
    if len(info) == 2:
        return info[1]
    elif len(info) == 3:
        return info[2]
    else:
        raise IndexError("Link is incomplete!")

def get_channel_id_from_video_id(video_id: str):
    youtube = get_auth_service()
    ans = youtube.videos().list(
        part="snippet,contentDetails",
        id=video_id
    ).execute()

    items = ans['items']
    video = items[0]
    snipp = video['snippet']
    ch_id = snipp['channelId']
    return ch_id

def get_channel_id_from_video_url(video_url: str):
    video_id = get_video_id_from_video_url(video_url)
    channel_id = get_channel_id_from_video_id(video_id)
    return channel_id