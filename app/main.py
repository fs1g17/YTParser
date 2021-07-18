from typing import Optional
from fastapi import FastAPI, File, UploadFile, Request
import psycopg2
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