from webbrowser import get
from fastapi import FastAPI, Request, Depends, WebSocket, File
from fastapi.datastructures import UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from six import viewkeys
from sqlalchemy.sql.expression import desc, select
from starlette.routing import request_response
from sqlalchemy import text 
from routers import auth 
from routers import creators as youtubers
from routers import latest_links
from routers import keyword_search
from handlers.gui import *
import csv 
import asyncio 
from io import TextIOWrapper

from sqlalchemy.orm import Session
from db.database import *
import json
from datetime import date, datetime

from handlers.DBHandler import cache, get_creators_range, cache_range, search_keywords, update_db_channel, remove_creator_videos
from handlers.YTHandler import *

# import alembic.config
# alembicArgs = [
#     '--raiseerr',
#     'upgrade', 'head'
# ]
# alembic.config.main(argv=alembicArgs)

app = FastAPI()
app.include_router(auth.router)
app.include_router(youtubers.router)
app.include_router(latest_links.router)
app.include_router(keyword_search.router)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = "POOPY"
    return templates.TemplateResponse("home_page.html", {"request": request, "data": data})

app.add_api_websocket_route("/latestLinks/ws", latest_links.websocket_get_links)
app.add_api_websocket_route("/keywords/ws", keyword_search.websocket_get_keywords)

@app.get("/getUniqueCreatorsVideos")
def get_uniq_creators_vids(db: Session = Depends(get_db)):
    try:
        results = db.execute("SELECT DISTINCT channel_id FROM videos;")
        ch_ids = []
        for row in results:
            ch_ids.append(row[0])

        name = []
        for channel_id in ch_ids:
            result = db.query(Creator).filter(Creator.channel_id == channel_id)
            for row in result:
                name.append(row)

        return {"success!":name}
    except Exception as e:
        return {"failed":str(e)}

@app.get("/cacheRange")
def cache_test(start: int, size: int, db: Session = Depends(get_db)):
    try:
        messages = cache_range(start=start,size=size,db=db)
        return {"success!":messages}
    except Exception as main_exception:
        return {"failure in main":str(main_exception)}

#TODO: it looks like the app is skipping click on car "62" completely!
@app.get("/checkRange")
def cache_check(start: int, size: int, db: Session = Depends(get_db)):
    try:
        creators = get_creators_range(start=start,size=size,db=db)
        done = []
        for creator in creators:
            channel_name = creator.channel_name
            id = creator.id
            done.append([id,channel_name])
        return {"success!":str(done)}
    except Exception as e:
        return {"Main: failed ":str(e)}

@app.get("/showCreators")
def show_creators(start:int = 1, limit: int = 230, db: Session = Depends(get_db)):
    try:
        results = db.query(Creator).offset(start).limit(limit).all()
        rows = []

        for creator in results:
            rows.append([creator.id,creator.channel_name,creator.channel_id])
        
        return {"success":rows}
    except Exception as e:
        return {"failure":str(e)}

@app.get("/showVideos")
def show_videos(start:int = 1, limit: int = 230, db: Session = Depends(get_db)):
    try:
        results = db.query(Video).order_by(desc(Video.date)).offset(start).limit(limit).all()
        rows = []

        for video in results:
            rows.append([video.date,video.channel_id])
        
        return {"success":rows}
    except Exception as e:
        return {"failure":str(e)}   