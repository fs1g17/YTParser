from typing import Optional
from webbrowser import get
from fastapi import FastAPI, File, UploadFile, Request
from google.oauth2 import credentials
import psycopg2
from pyasn1.type.univ import Null
import requests
import shutil
#from YTParser import get_auth_service,get_latest_video_description,get_links,filter_links,parse,parse_test,parse_save
from YTParser import *

dbname = "youtube"
tbname = "creators"

app = FastAPI()

@app.post("/uploadfile")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    return {"contents": contents}

@app.post("/saveInput")
async def save_file(file: UploadFile = File(...)):
    conn = psycopg2.connect(dbname=dbname,user="postgres", password="root", host="host.docker.internal")
    cursor = conn.cursor()

    try:
        command = "INSERT INTO " + tbname + " VALUES (%s,%s);"
        contents = await file.read()
        finished = await parse_save(contents,cursor,command)
    except:
        finished = False
    finally:
        conn.commit()
        cursor.close()
        conn.close()

    return {"finished":finished}

@app.post("/pgTest") 
def test():
    conn = psycopg2.connect(dbname=dbname,user="postgres", password="root", host="host.docker.internal")
    cursor = conn.cursor()

    try:
        command = "INSERT INTO " + tbname + " VALUES (%s,%s);"
        cursor.execute(command,("pewds","UC-lHJZR3Gqxm24_Vd_AJ5Yw"))
    except:
        command = "failed"
    finally:
        conn.commit()
        cursor.close()
        conn.close()

    return {"command":command}

@app.post("/apiTest")
def api_test():
    print("testing api")
    channel_id = "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
    description = get_latest_video_description(channel_id)
    return {"description":description}

@app.post("/getLinks")
def get_links():
    conn = psycopg2.connect(dbname=dbname,user="postgres", password="root", host="host.docker.internal")
    cursor = conn.cursor()

    try:
        command = "SELECT * FROM " + tbname + ";"
        result = get_latest_video_description(cursor,command)
    except:
        result = "Failure"
    finally:
        cursor.close()
        conn.close()
    
    return {"result":result}

@app.post("/wtf")
async def wtf():
    conn = psycopg2.connect(dbname=dbname,user="postgres", password="root", host="host.docker.internal")
    cursor = conn.cursor()

    ids = []
    try:
        cursor.execute("SELECT * FROM creators LIMIT 10")
        rows = cursor.fetchall()

        for row in rows:
            description = await get_latest_video_description(row[1])
            links = get_links(description)
            filtered_links = filter_links(links)
            ids += filtered_links
    except:
        ids.append("failure")
    finally:
        cursor.close()
        conn.close()

    return {"ids":ids}

@app.post("/getLink")
async def auth():
    if os.path.exists("CREDENTIALS_PICKLE_FILE"):
        return {"finished":"User already verified!"}
    
    url,flow = get_auth_service_link()
    return {"URL":url}

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