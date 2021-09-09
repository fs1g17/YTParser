from hashlib import new
from sqlalchemy.orm import query
from sqlalchemy.sql.expression import desc, select
from .authentication import *
from .YTHandler import *
from datetime import date, datetime
#from db.models import Creator, Video, Keyword
from db.database import Creator, Video
import json
from sqlalchemy.orm.session import Session
from sqlalchemy import text, desc

def get_creators(db: Session):
    # LIMIT FOR TESTING PURPOSES
    # results = db.execute("SELECT * FROM creators LIMIT 1;")
    #results = db.execute("SELECT * FROM creators;")
    results = db.query(Creator).all()
    return results

def get_creators_range(start: int, size: int, db: Session):
    return db.query(Creator).filter(text("id >= %s AND id < %s"%(start,start+size)))

def cache(db: Session):
    messages = []
    creators = get_creators(db=db)
    messages.append("got creators: " + str(creators))

    try:
        youtube = get_auth_service()
        messages.append("got youtube service")
    except Exception as e:
        messages.append("Failed to get youtube service " + str(e))
        return messages
    
    for creator in creators:
        channel_name = str(creator[0])
        channel_id = str(creator[1])

        if verify_channel_with_youtube(channel_id=channel_id,youtube=youtube) < 1:
            messages.append("Failed to cache: " + channel_name)
            continue 

        try:
            now = datetime.now()
            videos = get_videos_by_date_change(channel_id=channel_id,youtube=youtube,start_date=now,year=0,month=-1,day=0)
            #videos = get_videos_by_date_change(channel_id,youtube,now,0,-1,0)
        except Exception as e:
            messages.append("Failed to get youtube videos for " + channel_name + str(e))
            return messages

        for video in videos:
            video_id = get_video_id(video)
            video_date = get_datetime(video).date()
            video_view = get_views(video,youtube)
            video_desc = get_description(video)

            try:
                to_add = Video(
                    channel_id=channel_id,
                    video_id=video_id,
                    date=video_date,
                    views=int(video_view),
                    description=video_desc
                )
                db.add(to_add)
            except Exception as e:
                messages.append("Failed to add video: " + channel_name + " " + str(video_id) + " : " + str(e))
    return messages

def clean_input(input: str) -> str:
    input = input.replace("\n\n"," ")
    input = input.replace("\\n", " ")
    input = input.replace("\n", " ")
    return input 

def remove_creator_videos(channel_id: str, db: Session):
    db.execute("DELETE FROM videos WHERE channel_id='%s';"%channel_id)

def cache_range(start: int, size: int, db: Session):

    messages = {}

    completed = []
    failed = []
    general = []

    messages['completed'] = completed 
    messages['failed'] = failed 
    messages['general'] = general
    try:
        creators = get_creators_range(start=start,size=size,db=db)
        general.append("got creators")
    except Exception as e1:
        failed.append("DBHandler: Failed getting creators: " + str(e1))
        return messages
    try:
        youtube = get_auth_service()
        completed.append("got youtube service")
    except Exception as e2:
        failed.append("DBHandler: Failed to get youtube service " + str(e2))
        return messages
    
    for creator in creators:
        channel_name = creator.channel_name
        channel_id = creator.channel_id

        if verify_channel_with_youtube(channel_id=channel_id,youtube=youtube) < 1:
            failed.append("DBHandler: Failed to cache: " + channel_name)
            continue 

        try:
            now = datetime.now()
            videos = get_videos_by_date_change(channel_id=channel_id,youtube=youtube,start_date=now,year=-1,month=0,day=0)
        except Exception as e3:
            print("DBHANDLER EXCEPTION")
            print(str(e3))
            #e3 = str(e3).replace("\r","").replace("\n","")
            failure = {'channel_id':channel_id,'video_id':video_id,"exception":str(e3)}
            failed.append("DBHandler: Failed " + str(failure))
            continue 

        for video in videos:
            video_id = get_video_id(video)
            video_date = get_datetime(video)
            video_view = get_views(video,youtube)
            video_desc = get_description(video)
            video_desc = clean_input(video_desc)

            if db.query(Video.video_id).filter_by(video_id=video_id).first() is not None:
                failure = {'channel_id':channel_id,'video_id':video_id,"exception":"VIDEOS already CACHED"}
                failed.append("DBHandler: Skipping video as it's already cached " + str(failure))
                continue  

            try:
                to_add = Video(
                    channel_id=channel_id,
                    video_id=video_id,
                    date=video_date,
                    views=int(video_view),
                    description=video_desc
                )

                db.add(to_add)
            except Exception as e4:
                failure = {'channel_id':channel_id,'video_id':video_id,'exception':str(e4)}
                failed.append("DBHandler: Failed to add video. " + str(failure))
        db.commit()
        completed.append("completed caching for: " + str(channel_name))
    return messages

    # TODO: update cache function!

# get videos whose description matches any one of the keywords!
def search_keywords(keywords: List[str], db: Session) -> List[Tuple[Video,List[str]]]:
    videos = []

    for video in db.query(Video).order_by(desc(Video.date)).all():
        description = video.description
        matched_keywords = []
        for keyword in keywords:
            if keyword.lower() in description.lower():
                matched_keywords.append(keyword)
        if len(matched_keywords) > 0:
            videos.append([video,matched_keywords])
    return videos 

# returns dictionary mapping of channel_id to channel_name
def get_channel_names_ids(db: Session) -> dict:
    channel_names_ids = {}
    for creator in db.query(Creator).all():
        channel_name = creator.channel_name
        channel_id = creator.channel_id

        channel_names_ids[channel_id] = channel_name
    return channel_names_ids

def get_latest_video_db(db:Session, channel_id: str) -> Video:
    result = db.query(Video).filter(Video.channel_id==channel_id).order_by(desc(Video.date)).first()
    return result

def update_db_channel(db: Session, channel_id: str, youtube: googleapiclient.discovery.Resource):
    messages = []

    try:
        latest_video = get_latest_video_db(db=db,channel_id=channel_id)
        latest_video_id = latest_video.video_id
        latest_video_datetime = datetime.combine(latest_video.date, datetime.min.time())
        messages.append("got latest video from db!")
    except Exception as e:
        messages.append("failed: " + str(e))
        return messages

    try:
        new_videos = get_new_uploads(channel_id=channel_id,
                                     youtube=youtube,
                                     db_last_video_date=latest_video_datetime,
                                     db_last_video_id=latest_video_id)
        messages.append("got latest videos!")
    except Exception as e:
        messages.append("failed to get latest videos: " + str(e))
        return messages

    if len(new_videos) == 0: 
        messages = ["is already up to date!"] + messages
        return messages

    for video in new_videos:
        video_id = get_video_id(video)
        video_date = get_datetime(video)
        video_view = get_views(video,youtube)
        video_desc = get_description(video)
        video_desc = clean_input(video_desc)

        if db.query(Video.video_id).filter_by(video_id=video_id).first() is not None:
            failure = {'channel_id':channel_id,'video_id':video_id,'exception':str(e)}
            messages.append("DBHandler: Skipping video as it's already cached " + str(failure))
            continue  

        try:
            to_add = Video(
                channel_id=channel_id,
                video_id=video_id,
                date=video_date,
                views=int(video_view),
                description=video_desc
            )

            db.add(to_add)
        except Exception as e:
            failure = {'channel_id':channel_id,'video_id':video_id,'exception':str(e)}
            messages.append("DBHandler: Failed to add video. " + str(failure))
    db.commit()
    messages.append("completed updating for: " + str(channel_id))
    return messages

#------------ MOVED TO keyword_search.py in /app/routers/ so that live updates could be reflected on the page! ------------------
# def update_db(db: Session):
#     messages = []
#     completed = []
#     failed = []
#     channel_names_ids = get_channel_names_ids(db)

#     try:
#         youtube = get_auth_service()
#         messages.append("got youtube service")
#     except Exception as e:
#         messages.append("failed to get youtube service: " + str(e))
#         return messages 
    
#     for channel_id,channel_name in channel_names_ids.items():
#         channel_exists = verify_channel_with_youtube(channel_id=channel_id,youtube=youtube)

#         if not(channel_exists):
#             failed.append("channel %s %s doesn't exist on youtube anymore!"%(channel_name,channel_id))
#             continue
        
#         channel_messages = update_db_channel(db=db,youtube=youtube,channel_id=channel_id)
#         messages += channel_messages
#         completed.append(channel_name)
    
#     return messages,completed,failed 





# 0.) Verify channel exists!
# 1.) check if latest video date matches with latest video on YouTube
# 2.) if it doesn't match, get videos after latest video in db 
# 3.) cache all those videos!
# N.B: check the channel exists!
