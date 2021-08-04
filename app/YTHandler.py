from authentication import *
import re
from datetime import datetime 
filters = ['vk','music','instagram','tiktok']

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

#----------------------- CHANNEL FUNCTIONS ----------------------------------------
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

#------------------------ BULK OPERATIONS ------------------------------------------
def parse_date(date:str):
    date = datetime.strptime(date,'%Y-%m-%dT%H:%M:%SZ')
    return date

# need to make sure the numbers are in range!!
# month can't be more than 12, day can't be more than #days in month!
# TODO: this ^^
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