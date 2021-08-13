from .authentication import *
from .YTHandler import *
from datetime import date, datetime
#from app.db.models import Creator, Video, Keyword
from db.models import Creator, Video, Keyword
#from app.db.models import *
import ast
from sqlalchemy.orm.session import Session

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
        video_id = get_video_id(video)

        # if video is already cached, skip 
        if db.execute("SELECT * FROM videos WHERE channel_id='%s' AND video_id='%s'"%(channel_id,video_id)).rowcount > 0:
            continue 

        video_date = get_date(video)
        video_view = get_views(video,youtube)
        video_desc = get_description(video)
        video_info = {"date":video_date,"views":video_view,"description":video_desc}

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

def get_latest_video_date_db(channel_id: str, db: Session):
    results = db.execute("SELECT * FROM videos WHERE channel_id='%s'"%channel_id)
    
    latest_date = datetime.now()
    latest_date = latest_date.replace(year=latest_date.year-1)

    for row in results:
        video_info = ast.literal_eval(row[2])
        date = parse_date(video_info['date'])
        if date > latest_date: 
            latest_date = date 
    return latest_date

def get_all_channel_ids(db: Session):
    results = db.execute("SELECT channel_id FROM creators;")
    channel_ids = []

    for row in results:
        channel_ids.append(row)

    return channel_ids

def cache_videos_to_db(videos: List[dict]):
    pass

def update_db(db: Session):
    messages = []
    channel_ids = get_all_channel_ids(db)
    messages.append("got channel ids")
    youtube = get_auth_service()
    messages.append("got youtube service")
    messages.append("-----------------")

    format = "%d%M%Y"

    final_message = "db is up to date!"

    for ch_id in channel_ids:
        try:
            channel_id = str(ch_id[0])
            messages.append("looking at channel "+channel_id)
            date_db = get_latest_video_date_db(channel_id,db)
            messages.append("date_db: " + date_db.strftime(format))
            date_yt = get_latest_video_date_yt(channel_id,youtube)
            messages.append("date_yt:" + date_yt.strftime(format))

            if date_db.strftime(format) != date_yt.strftime(format):
                videos = get_videos_from_date_onward(youtube,channel_id,date_db)

                for video in videos:
                    video_id = get_video_id(video)

                    if db.execute("SELECT * FROM videos WHERE channel_id='%s' AND video_id='%s'"%(channel_id,video_id)).rowcount > 0:
                        continue 

                    video_date = get_date(video)
                    video_view = get_views(video,youtube)
                    video_desc = get_description(video)
                    video_info = {"date":video_date,"views":video_view,"description":video_desc}

                    to_add = Video(
                        channel_id = str(channel_id),
                        video_id = str(video_id),
                        video_info = str(video_info)
                    )
                    db.add(to_add)
                    final_message = "db updated!"
        except Exception as e:
            messages.append("ERROR: " + str(e))
    
    return [final_message] + messages
