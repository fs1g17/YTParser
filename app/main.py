from webbrowser import get
from fastapi import FastAPI, Request, Depends, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from six import viewkeys
from sqlalchemy.sql.expression import select
from starlette.routing import request_response
from sqlalchemy import text 
from routers import auth 
from routers import creators as youtubers
from routers import latest_links
from routers import keyword_search
from handlers.gui import *
import csv 

from sqlalchemy.orm import Session
from db.database import *
import json
from datetime import date, datetime

from handlers.DBHandler import cache, get_creators_range, cache_range
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
    return templates.TemplateResponse("page.html", {"request": request, "data": data})

app.add_api_websocket_route("/latestLinks/ws", latest_links.websocket_get_links)
app.add_api_websocket_route("/keywords/ws", keyword_search.websocket_get_keywords)

@app.get("/cacheRange")
def cache_test(start: int, size: int, db: Session = Depends(get_db)):
    try:
        messages = cache_range(start=start,size=size,db=db)
        db.commit()
        return {"success!":str(messages['general']),"failed":str(messages['failed']),"completed":str(messages['completed'])}
    except Exception as e:
        return {"failure in main":str(e)}

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

@app.get("/topCreator")
def get_top(limit: int, db: Session = Depends(get_db)):
    try:
        rows = [] 
        results = db.query(Creator).filter(text("id<%s"%limit))

        for row in results:
            rows.append(row)
        return {"rows":rows}
    except Exception as e:
        return {"error":str(e)}

@app.get("/topVideos")
def get_top_vids(limit: int, db: Session = Depends(get_db)):
    try:
        rows = [] 
        results = db.query(Video).limit(limit).all()

        for row in results:
            rows.append(row)
        return {"rows":rows}
    except Exception as e:
        return {"error":str(e)}

@app.get("/getSlice")
def get_slice(start: int, size: int, db: Session = Depends(get_db)):
    try:
        rows = []
        results = db.query(Creator).filter(text("id >= %s AND id < %s"%(start,start+size)))
        for row in results:
            rows.append(row)
        return {"rows":rows}
    except Exception as e:
        return {"error":str(e)}

@app.get("/getCreatorsVideos")
def get_creators_videos(channel_index: int, db: Session = Depends(get_db)):
    try:
        creator = db.query(Creator).filter(Creator.id == channel_index).first()
        channel_id = creator.channel_id
    except Exception as e:
        return {"Failed": str(e)}

    try:
        rows = [] 
        results = db.execute("SELECT * FROM videos WHERE channel_id='%s';"%channel_id)
        for row in results:
            rows.append(row)
        return {"success!":str(rows)}
    except Exception as e:
        return {"Fail":str(e)}


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