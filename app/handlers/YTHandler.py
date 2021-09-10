from time import strftime
from typing import List, Tuple

from sqlalchemy.orm.session import Session
from .authentication import *
import re
from datetime import datetime 
import ast 
filters = ['vk','music','instagram','tiktok','youtube']

#--------------- VIDEO FUNCTIONS -------------------------
# N.B: YouTube API returns query result as a dictionary 
# All of these functions are helper functions to unwrap data 

#raise KeyError('video publish date missing, video could have been DELETED: %s'%str(video))
def get_date(video: dict) -> str:
    content_details = video['contentDetails']

    if not('videoPublishedAt' in content_details):
        snippet = video['snippet']
        date = snippet['videoPublishedAt']
        return date

    date = content_details['videoPublishedAt']
    return date 

def get_datetime(video: dict) -> datetime:
    content_details = video['contentDetails']
    date = content_details['videoPublishedAt']
    form = '%Y-%m-%dT%H:%M:%SZ'
    return datetime.strptime(date,form)

def get_title(video: dict) -> str:
    snippet = video['snippet']
    title = snippet['title']
    return title

def get_description(video: dict) -> str:
    snippet = video['snippet']
    description = snippet['description']
    return description

def get_views(video: dict, youtube: googleapiclient.discovery.Resource) -> str:
    video_id = video['contentDetails']['videoId']

    ans = youtube.videos().list(
        part="statistics",
        id=video_id
    ).execute()

    items = ans['items'][0]
    stats = items['statistics']
    views = stats['viewCount']
    return views

def get_link(video: dict) -> str:
    snippet = video['snippet']
    resource = snippet['resourceId']
    video_id = resource['videoId']
    base_url = "https://www.youtube.com/watch?v="
    return base_url + video_id

def get_video_id(video: dict) -> str:
    snippet = video['snippet']
    resource = snippet['resourceId']
    video_id = resource['videoId']
    return video_id

def get_channel_id(video: dict) -> str:
    snippet = video['snippet']
    channel_id = snippet['channelId']
    return channel_id

def get_latest_video(channel_id:str) -> dict:
    youtube = get_auth_service()
    return get_latest_video_with_yt(channel_id=channel_id,youtube=youtube)

def get_latest_video_with_yt(channel_id:str, youtube: googleapiclient.discovery.Resource) -> dict:
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
    return latest_video

def get_latest_video_description(channel_id:str, youtube:googleapiclient.discovery.Resource) -> str:
    latest_video = get_latest_video_with_yt(channel_id,youtube)
    latest_video_description = latest_video['snippet']['description']
    return latest_video_description

def get_latest_video_date_yt(channel_id:str, youtube: googleapiclient.discovery.Resource):
    latest_video = get_latest_video_with_yt(channel_id,youtube)
    date = get_date(latest_video)
    date = parse_date(date)
    return date

def get_latest_video_date_id_yt(channel_id:str, youtube: googleapiclient.discovery.Resource) -> Tuple[datetime, str]:
    latest_video = get_latest_video_with_yt(channel_id,youtube)
    date = get_date(latest_video)
    date = parse_date(date)
    video_id = get_video_id(latest_video)
    return date, video_id

def get_links(description: str) -> List[str]:
    return re.findall("(?P<url>https?://[^\s]+)", description)

def filter_links(links: List[str]) -> List[str]:
    return [link for link in links if not re.search("|".join(["("+f+")" for f in filters]),link)]

def get_latest_links(channel_id:str, youtube:googleapiclient.discovery.Resource) -> List[str]:
    if verify_channel_with_youtube(channel_id,youtube) < 1:
        return ["CHANNEL_DOESN'T_EXIST"]
    description = get_latest_video_description(channel_id,youtube)
    links = get_links(description)
    filtered_links = filter_links(links)
    return filtered_links

#-------------- CHANNEL FUNCTIONS -----------------------------
def verify_channel(channel_id: str) -> int:
    if not(is_auth()):
        return -1
    youtube = get_auth_service()
    return verify_channel_with_youtube(channel_id=channel_id,youtube=youtube)

def verify_channel_with_youtube(channel_id: str, youtube:googleapiclient.discovery.Resource) -> int:
    if not(is_auth()):
        return -1

    response = youtube.channels().list(
        part="snippet",
        id=channel_id
    ).execute()

    page_info = response["pageInfo"]
    total_results = page_info["totalResults"]

    return total_results

def parse_date(date_string: str) -> datetime:
    return datetime.strptime(date_string,'%Y-%m-%dT%H:%M:%SZ')

def change_date(start: datetime, dy: int, dm: int, dd: int) -> datetime:
    year = start.year + dy
    month = start.month + dm
    day = start.day + dd
    return start.replace(year=year,month=month,day=day)

def get_uploads(channel_id: str, youtube:googleapiclient.discovery.Resource) -> dict:
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

def get_uploads_next_page(channel_id: str, next_page_token: str, youtube:googleapiclient.discovery.Resource) -> dict:
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

def get_videos_by_date_change(channel_id: str, youtube:googleapiclient.discovery.Resource, start_date: datetime, year: int, month: int, day: int) -> List[dict]:
    end_date = change_date(start_date,year,month,day)

    #playlist = get_uploads(channel_id,youtube)
    playlist = get_uploads(channel_id=channel_id,youtube=youtube)
    next_page_token = ""
    if 'nextPageToken' in playlist:
        next_page_token = playlist['nextPageToken']
    videos = playlist['items']
    
    curr_date = parse_date(get_date(videos[0]))
    #curr_date = datetime.now()
    all_videos = []
    while(curr_date >= end_date):
        for video in videos:
            if get_title(video=video) == 'Deleted video':
                continue 

            if curr_date > start_date:
                continue
            curr_date = parse_date(get_date(video))

            if curr_date < end_date:
                break
            all_videos.append(video)

        if not(next_page_token == ""):
            playlist = get_uploads_next_page(channel_id=channel_id,next_page_token=next_page_token,youtube=youtube)
            if 'nextPageToken' in playlist:
                next_page_token = playlist['nextPageToken']
            else:
                next_page_token = ""
            videos = playlist['items']
        else:
            break 
    return all_videos

#TODO: implement check here!
#if get_title(video=video) == 'Deleted video':
def get_new_uploads(channel_id: str, youtube: googleapiclient.discovery.Resource, db_last_video_id: str, db_last_video_date: datetime):
    playlist = get_uploads(channel_id=channel_id,youtube=youtube)
    next_page_token = ""
    if 'nextPageToken' in playlist:
        next_page_token = playlist['nextPageToken']
    videos = playlist['items']

    curr_video_id = get_video_id(videos[0])
    curr_date = parse_date(get_date(videos[0]))
    all_videos = []
    while(curr_video_id != db_last_video_id) and (curr_date >= db_last_video_date):
        for video in videos:
            curr_video_id = get_video_id(video=video)
            curr_date = parse_date(get_date(video))
            if (curr_video_id == db_last_video_id) or (curr_date < db_last_video_date) :
                break
            
            all_videos.append(video)

        if not(next_page_token == ""):
            playlist = get_uploads_next_page(channel_id=channel_id,next_page_token=next_page_token,youtube=youtube)
            if 'nextPageToken' in playlist:
                next_page_token = playlist['nextPageToken']
            else:
                next_page_token = ""
            videos = playlist['items']
        else:
            break 
    return all_videos

# what if video was deleted!!!?? -> don't let it go past last video date! simples ;)