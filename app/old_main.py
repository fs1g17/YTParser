import ast
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Request, Depends
from fastapi.param_functions import Body 
from google.oauth2 import credentials
import psycopg2
from pyasn1.type.univ import Null
import requests
import shutil
import json
from datetime import datetime

from sqlalchemy.sql.expression import desc
from db.schemas import AddCreator
from sqlalchemy.orm import Session
from sqlalchemy import select 
from db.database import get_db
from db.models import Creator
from db.database import validate_database
from handlers.YTHandler import *
from handlers.DBHandler import *
from handlers.authentication import *

dbname = "youtube"
tbname = "creators"

app = FastAPI()

import alembic.config
alembicArgs = [
    '--raiseerr',
    'upgrade', 'head'
]
alembic.config.main(argv=alembicArgs)

keywords = ["bridgestone",
            "michelin",
            "continental",
            "nokian",
            "kumho",
            "goodyear",
            "hankook",
            "pirelli",
            "yokohama",
            "dunlop",
            "marshal crugen",
            "tigar",
            "formula",
            "viatti",
            "kormoran",
            "semperit",
            "toyo",
            "tunga",
            "matador",
            "nexen",
            "cordiant",
            "nitto",
            "msxxis",
            "laufen",
            "debica",
            "kama",
            "nankang",
            "tristar",
            "cst",
            "contyre",
            "roadstone",
            "cooper",
            "bfgoodrich",
            "general tire",
            "gislaved",
            "triangle"]

# Sponsor - Channel name - Date - Views - Link 

@app.post("/search/allKeywords")
def search_all_keywords(db: Session = Depends(get_db)):
    output = []
    answer = []
    i = 0
    try:
        results = db.execute("SELECT * FROM videos")

        for row in results:
            video_info = ast.literal_eval(row[2])
            description = video_info['description']
            description = description.lower()

            for keyword in keywords:
                if keyword in description:
                    channel_id = row[0]
                    video_id = row[1]
                    date = video_info['date']
                    views = video_info['views']
                    link = "youtube.com/watch?v=" + video_id
                    line = [keyword,channel_id,date,views,link] 

                    output.append(line)

        for line in output:
            channel_id = line[1]
            channel_name = ""
            result = db.execute("SELECT * FROM creators WHERE channel_id='%s'"%channel_id)
            
            for row in result:
                channel_name = row[0]

            ans = line 
            ans[1] = channel_name
            answer.append(ans)
                
    except Exception as e:
        return {"error":str(e),"output":output}
    
    return {"finished":True,"answer":answer}

@app.get("/update")
def update(db: Session = Depends(get_db)):
    try:
        messages = update_db(db)
        db.commit()
        return {"messages":messages}
    except Exception as e:
        return {"error":str(e)}

@app.post("/search/creatorKeyword")
def search_creator_keyword(creator: str, keyword:str, db: Session = Depends(get_db)):
    matches = []
    return matches

@app.post("/search/keyword")
def search_keyword(keyword:str, db: Session = Depends(get_db)):
    matches = []
    try:
        results = db.execute("SELECT * FROM videos")

        for row in results:
            video_info = ast.literal_eval(row[2])
            description = video_info['description']

            if keyword in description:
                matches.append(row)

            if len(matches) > 10:
                return matches
    except Exception as e:
        return {"error":str(e),"video_info":row[2]}

    return {"matches":matches}

@app.post("/sizeOfTable")
def get_size_of_table(table: str, db: Session = Depends(get_db)):
    try:
        return {"size of " + table : str(db.execute("SELECT * FROM " + table).rowcount)}
    except Exception as e:
        return {"error":str(e)}


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
        num = results.rowcount

        if end > num:
            return {"outside of range"}
        

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