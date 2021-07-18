from typing import Optional
from fastapi import FastAPI, File, UploadFile
import psycopg2
import requests
import shutil
from YTParser import get_auth_service,get_latest_video_description,get_links,filter_links,parse,parse_test

app = FastAPI()

@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    return {"contents": contents}

