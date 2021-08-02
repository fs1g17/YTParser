from typing import Optional
from webbrowser import get
from fastapi import FastAPI, File, UploadFile, Request, Depends
from fastapi.param_functions import Body 
from google.oauth2 import credentials
import psycopg2
from pyasn1.type.univ import Null
import requests
import shutil
from schemas import AddCreator
from sqlalchemy.orm import Session
from sqlalchemy import select 
from database import get_db
from YTParser import *
from models import Creator
from database import validate_database
dbname = "youtube"
tbname = "creators"

app = FastAPI()

import alembic.config
alembicArgs = [
    '--raiseerr',
    'upgrade', 'head'
]
alembic.config.main(argv=alembicArgs)

@app.post("/deleteVideoByNumber")
def del_by_num(start:int, end:int, db: Session = Depends(get_db)):
    exceptions = []
    try:
        results = db.execute("SELECT * FROM creators;")
        for i,row in enumerate(results):
            if i < start:
                continue
            if i > end:
                db.commit()
                return {"finished":True}
            try:
                channel_name = row[0]
                channel_id = row[1]
                db.execute("DELETE FROM videos WHERE channel_id='%s';"%channel_id)
            except Exception as exception:
                exceptions.append(str((channel_name,exception)))
    except Exception as e:
        return {"error":str(e)}

@app.post("/cacheVideosByNumber")
def cache_onwards_number(start:int, end:int, db: Session = Depends(get_db)):
    exceptions = []
    try:
        results = db.execute("SELECT * FROM creators;")
        for i,row in enumerate(results):
            if i < start:
                continue 

            if i > end: 
                return {"finished":"True","exceptions":exceptions}

            try:
                channel_name = row[0]
                cache_to_db(db,channel_name)
                db.commit()
            except Exception as exception:
                exceptions.append(str((channel_name,exception)))
    except Exception as e:
        exceptions.append(str(("general exception", e)))
    
    return {"errors":exceptions}

@app.get("/getCreators")
def get_creators(db: Session = Depends(get_db)):
    try:
        results = db.execute("SELECT channel_name FROM creators;")
        return {"creators":results}
    except Exception as e:
        return {"error":str(e)}

@app.post("/addCreator")
def add_creator(db: Session = Depends(get_db), details: AddCreator = Body(...)):
    try:
        validate_database()
    except Exception as e:
        return {"error":str(e)}
    
    try:
        to_create = Creator (
            channel_name = details.channel_name,
            channel_id = details.channel_id
        )
        db.add(to_create)
        db.commit()
    except Exception as e:
        return {"error":str(e)}
    
    return {
        "success":True,
    }

@app.post("/removeCreator")
def del_creator(channel_name: str, db: Session = Depends(get_db)):
    try:
        db.execute("DELETE FROM creators WHERE channel_name = '%s'"%(channel_name))
        db.commit()
    except Exception as e:
        return {"error":str(e)}

    return {"success":True}

@app.get("/getTop")
def get_top(table:str, limit: int, db: Session = Depends(get_db)):
    try:
        rows = []
        results = db.execute("SELECT * FROM " + table + " LIMIT " + str(limit))
        for row in results:
            rows.append(row)
        return {"rows":rows}
    except Exception as e:
        return {"error":str(e)}

@app.post("/saveInput")
async def save_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        bytes_io = io.BytesIO(contents)
        opened_file = io.TextIOWrapper(bytes_io,encoding="UTF-8")
        reader = csv.reader(opened_file)

        for row in reader:
            try:
                channel_name = row[0].replace("'","\'")
                channel_id = row[2]
                db.execute("INSERT INTO creators VALUES ('" + channel_name + "', '" + channel_id + "')")
                print("done: " + str(channel_name))
            except Exception as e:
                print("error: " + str(e))

        db.commit()
    except Exception as e:
        return {"BIG error":str(e)}

    return {"success":True}

@app.post("/getAuthLink")
async def auth():
    if os.path.exists("CREDENTIALS_PICKLE_FILE"):
        return {"finished":"User already verified!"}
    
    url,flow = get_auth_service_link()
    return {"URL":url[0]}

#TODO: figure out how to save stuff in python docker container locally!! (using volumes I guess)
@app.get("/setCode")
def set_code(code):
    try:
        _,flow = get_auth_service_link()
        auth = get_credentials(flow,code)
        with open("CREDENTIALS_PICKLE_FILE", 'wb') as f:
            pickle.dump(auth, f)
    except:
        return {"finished":False}
    return {"finished":True}

#-----------------LEGACY--------------------------
# @app.post("/cacheDB")
# def cache_2_db(channel_name: str, db: Session = Depends(get_db)):
#     try:
#         cache_to_db(db,channel_name)
#         db.commit()
#     except Exception as e:
#         return {"error":str(e)}
#     return {"success":True}

# @app.post("/deleteVideosByChannelId")
# def delete_videos_by_channel_id(channel_id: str, db: Session = Depends(get_db)):
#     try:
#         db.execute("DELETE FROM videos WHERE channel_id='%s';"%channel_id)
#         db.commit()
#     except Exception as e:
#         return {"error":str(e)}
#     return {"success":True}

# # select from which creator to cache onwards
# @app.post("/cacheVideosOnwards")
# def cache_onwards(channel_name:str, db: Session = Depends(get_db)):
#     exceptions = []
#     try:
#         results = db.execute("SELECT * FROM creators;")
#         condition = False 
#         for row in results:
#             try:
#                 ch_name = row[0]
#                 if condition or ch_name == channel_name:
#                     condition = True
#                     cache_to_db(db,channel_name)
#                     db.commit()
#             except Exception as exception:
#                 exceptions.append(str((ch_name,exception)))
        
#     except Exception as e:
#         exceptions.append(str(("general exception",e)))
    
#     return {"finished":True,"errors":exceptions}
#

# @app.post("/cacheVideos")
# def cache_videos(db: Session = Depends(get_db)):
#     print("COMMENCING CACHING")
#     exceptions = []
#     bloggers = []
#     try:
#         results = db.execute("SELECT * FROM creators;")

#         for row in results:
#             try:
#                 channel_name = row[0]
#                 print(channel_name)
#                 bloggers.append(channel_name)
#                 cache_to_db(db,channel_name)
#                 db.commit()
#             except Exception as exception:
#                 exceptions.append(str((channel_name,exception)))
        
#     except Exception as e:
#         exceptions.append(str(("general exception",e)))
    
#     return {"finished":True,"errors":exceptions}

# @app.post("/clearVideos")
# def clear_videos(db: Session = Depends(get_db)):
#     try:
#         db.execute("DELETE FROM videos;")
#         db.commit()
#     except Exception as e:
#         return {"error":str(e)}
#     return {"finished":True}