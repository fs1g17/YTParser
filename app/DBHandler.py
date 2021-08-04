from authentication import *
from datetime import datetime
from YTHandler import *
from models import *

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