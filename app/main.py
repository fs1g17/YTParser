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

from handlers.DBHandler import cache, get_creators_range, cache_range, search_keywords, update_db_channel
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

@app.post("/uploadCreatorList")
async def get_creators_list(db: Session = Depends(get_db), file: UploadFile = File(...)):
    try:

        with file.file as tempfile:
            with tempfile._file as csvfile:
                f = TextIOWrapper(csvfile, encoding='utf-8')
                reader = csv.reader(f)

                num = 1
                for row in reader:
                    channel_name = row[0]
                    channel_id = row[2]
                    to_add = Creator(
                        id=num,
                        channel_name=channel_name,
                        channel_id=channel_id
                    )
                    db.add(to_add)
                    num += 1
                db.commit()
        return {"success!":"added all creators to db"}
    except Exception as e:
        return {"failure":"error: %s"%str(e)}

@app.get("/showAllCreators")
async def show_all_creators(db: Session = Depends(get_db)):
    try:
        results = db.query(Creator).all()
        youtubers = []
        
        for ytb in results:
            youtubers.append([ytb[0],ytb[1],ytb[2]])
        return {"success!":youtubers}
    except Exception as e:
        return {"failure":str(e)}
# @app.get("/updateDB")
# def update(db: Session = Depends(get_db)):
#     try:
#         messages,completed,failed = update_db(db=db)
#         return {"messages":messages,"completed":completed,"failed":failed}
#     except Exception as e:
#         return {"failed in MAIN":str(e)}

# @app.get("/updateCreator")
# def update_creator(channel_id: str, db: Session = Depends(get_db)):
#     try:
#         messages = update_db_channel(channel_id=channel_id,db=db)
#         return {"success":messages}
#     except Exception as e:
#         return {"failure in MAIN":str(e)}

# @app.get("/cacheRange")
# def cache_test(start: int, size: int, db: Session = Depends(get_db)):
#     try:
#         messages = cache_range(start=start,size=size,db=db)
#         db.commit()
#         return {"success!":str(messages['general']),"failed":str(messages['failed']),"completed":str(messages['completed'])}
#     except Exception as e:
#         return {"failure in main":str(e)}

# @app.get("/checkRange")
# def cache_check(start: int, size: int, db: Session = Depends(get_db)):
#     try:
#         creators = get_creators_range(start=start,size=size,db=db)
#         done = []
#         for creator in creators:
#             channel_name = creator.channel_name
#             id = creator.id
#             done.append([id,channel_name])
#         return {"success!":str(done)}
#     except Exception as e:
#         return {"Main: failed ":str(e)}

# @app.get("/topCreator")
# def get_top(limit: int, db: Session = Depends(get_db)):
#     try:
#         rows = [] 
#         results = db.query(Creator).filter(text("id<%s"%limit))

#         for row in results:
#             rows.append(row)
#         return {"rows":rows}
#     except Exception as e:
#         return {"error":str(e)}

# @app.get("/topVideos")
# def get_top_vids(limit: int, db: Session = Depends(get_db)):
#     try:
#         rows = [] 
#         results = db.query(Video).limit(limit).all()

#         for row in results:
#             rows.append(row)
#         return {"rows":rows}
#     except Exception as e:
#         return {"error":str(e)}

# @app.get("/getSlice")
# def get_slice(start: int, size: int, db: Session = Depends(get_db)):
#     try:
#         rows = []
#         results = db.query(Creator).filter(text("id >= %s AND id < %s"%(start,start+size)))
#         for row in results:
#             rows.append(row)
#         return {"rows":rows}
#     except Exception as e:
#         return {"error":str(e)}

# @app.get("/getCreatorsVideos")
# def get_creators_videos(channel_index: int, db: Session = Depends(get_db)):
#     try:
#         creator = db.query(Creator).filter(Creator.id == channel_index).first()
#         channel_id = creator.channel_id
#     except Exception as e:
#         return {"Failed": str(e)}

#     try:
#         rows = [] 
#         results = db.query(Video).filter(Video.channel_id==channel_id).order_by(desc(Video.date)).all()
#         for video in results:
#             rows.append((video.date,video.video_id))
#         return {"success!":str(rows)}
#     except Exception as e:
#         return {"Fail":str(e)}



# @app.get("/getCreatorsVideos")
# def get_creators_videos(channel_index: int, db: Session = Depends(get_db)):
#     try:
#         creator = db.query(Creator).filter(Creator.id == channel_index).first()
#         channel_id = creator.channel_id
#     except Exception as e:
#         return {"Failed": str(e)}

#     try:
#         rows = [] 
#         results = db.execute("SELECT * FROM videos WHERE channel_id='%s';"%channel_id)
#         for row in results:
#             rows.append(row)
#         return {"success!":str(rows)}
#     except Exception as e:
#         return {"Fail":str(e)}

@app.get("/TEST")
def test(start: int, size: int, db: Session = Depends(get_db)):
    try:
        creators = db.query(Creator).offset(start).limit(size).all()
        rows = []
        for creator in creators:
            rows.append([creator.channel_name,creator.channel_id])
        return {"sucess":creators}
    except Exception as e:
        return {"failure":str(e)}

@app.get("/searchKeywords")
async def search(db: Session = Depends(get_db)):
    try:
        # do the keyword search here!
        loop = asyncio.get_event_loop()
        video_keywords = await loop.run_in_executor(None, search_keywords, keywords, db)
        output = [(video.video_id,sponsors)for video,sponsors in video_keywords]
        return {"success!":str(output)}
    except Exception as e:
        return {"failure!":str(e)}
        



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