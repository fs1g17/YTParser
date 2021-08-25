from sqlalchemy.orm import query
from sqlalchemy.sql.expression import desc, select
from .authentication import *
from .YTHandler import *
from datetime import date, datetime
#from db.models import Creator, Video, Keyword
from db.database import Creator, Video
import json
from sqlalchemy.orm.session import Session
from sqlalchemy import text 

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
    except Exception as e:
        failed.append("DBHandler: Failed getting creators: " + str(e))
        return messages
    try:
        youtube = get_auth_service()
        completed.append("got youtube service")
    except Exception as e:
        failed.append("DBHandler: Failed to get youtube service " + str(e))
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
            #videos = get_videos_by_date_change(channel_id=channel_id,youtube=youtube,start_date=now,year=0,month=-1,day=0)
            #videos = get_videos_by_date_change(channel_id,youtube,now,0,-1,0)
        except Exception as e:
            failed.append("DBHandler: Failed to get youtube videos for " + channel_name + str(e))
            continue 

        for video in videos:
            video_id = get_video_id(video)
            video_date = get_datetime(video)
            video_view = get_views(video,youtube)
            video_desc = get_description(video)
            video_desc = clean_input(video_desc)

            if db.query(Video.video_id).filter_by(video_id=video_id).first() is not None:
                failure = {'channel_id':channel_id,'video_id':video_id,'exception':str(e)}
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
            except Exception as e:
                failure = {'channel_id':channel_id,'video_id':video_id,'exception':str(e)}
                failed.append("DBHandler: Failed to add video. " + str(failure))
        #db.commit()
        completed.append("completed caching for: " + str(channel_name))
    return messages

    # TODO: update cache function!