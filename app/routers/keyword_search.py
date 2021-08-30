import os
import math
import asyncio
from starlette.websockets import WebSocket
from handlers.YTHandler import *
from handlers.DBHandler import search_keywords, get_channel_names_ids
from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from db.database import get_db
from db.database import Creator, Video

templates = Jinja2Templates(directory="templates")

router = APIRouter()

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

@router.get("/keywords", response_class=HTMLResponse)
async def keyword_endpoint(request: Request):
    if not(os.path.exists("CREDENTIALS_PICKLE_FILE")):
        heading = "You're not supposed to be here >:D"
        message = "Psst. Authenticate yourself!"
        return templates.TemplateResponse("blank.html", {"request":request,"heading":heading,"message":message})

    return templates.TemplateResponse("keywords.html", {"request":request})

async def websocket_get_keywords(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()

    video_keywords = None

    while True:
        data = await websocket.receive_json()
        action = data['action']
        if action == 'next':
            await websocket.send_json({"message":"got next"})

            if video_keywords == None:
                continue 
            if page >= max_page:
                continue
                
            page += 1 
            start = page*10 
            if len(video_keywords) - start < 10:
                subsection = video_keywords[start:]
            else:
                end = start + 10
                subsection = video_keywords[start:end]

            await websocket.send_json({"action":"clear"})
            
            #send_info(subsection)
            for video,sponsors in subsection:
                #Sponsor	Channel	Date	Views	Link
                sponsor = sponsors
                channel = channel_names_ids[video.channel_id]
                publish_date = str(video.date)
                views = video.views
                link = "youtube.com/watch?v=" + video.video_id
                await websocket.send_json({"sponsor":sponsor,"channel":channel,"date":publish_date,"views":views,"link":link})
        elif action == 'prev':
            await websocket.send_json({"message":"got prev"})

            if video_keywords == None:
                continue 
            if page == 0:
                continue

            page -= 1 
            start = page*10 
            end = start + 10

            await websocket.send_json({"action":"clear"})
            for video,sponsors in video_keywords[start:end]:
                #Sponsor	Channel	Date	Views	Link
                sponsor = sponsors
                channel = channel_names_ids[video.channel_id]
                publish_date = str(video.date)
                views = video.views
                link = "youtube.com/watch?v=" + video.video_id
                await websocket.send_json({"sponsor":sponsor,"channel":channel,"date":publish_date,"views":views,"link":link})
        elif action == 'add_keyword':
            new_keyword = data['keyword']
            keywords.append(new_keyword)
            await websocket.send_json({"message":"appended new keyword " + new_keyword})
        elif action == 'search':
            video_keywords = search_keywords(keywords=keywords,db=db)
            await websocket.send_json({"message":"got search"})

            page = 0
            max_page = math.floor(len(video_keywords)/10)

            channel_names_ids = get_channel_names_ids(db)
            for video,sponsors in video_keywords[:10]:
                #Sponsor	Channel	Date	Views	Link
                sponsor = sponsors
                channel = channel_names_ids[video.channel_id]
                publish_date = str(video.date)
                views = video.views
                link = "youtube.com/watch?v=" + video.video_id
                await websocket.send_json({"sponsor":sponsor,"channel":channel,"date":publish_date,"views":views,"link":link})
        else:
            await websocket.send_json({"message":"something went wrong"})