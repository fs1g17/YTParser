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
def get_top(db: Session = Depends(get_db)):
    try:
        rows = []
        results = db.execute("SELECT * FROM creators")
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

@app.post("/apiTest")
def api_test():
    print("testing api")
    channel_id = "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
    description = get_latest_video_description(channel_id)
    return {"description":description}

@app.post("/getAuthLink")
async def auth():
    if os.path.exists("CREDENTIALS_PICKLE_FILE"):
        return {"finished":"User already verified!"}
    
    url,flow = get_auth_service_link()
    return {"URL":url}

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