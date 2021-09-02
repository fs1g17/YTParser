import csv
import os
import math
import asyncio
from starlette.responses import FileResponse
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

russian_keywords = ["Авито","Авто.ру","Автоспот","Дром","СберАвто"]

@router.get("/keywords", response_class=HTMLResponse)
async def keyword_endpoint(request: Request):
    if not(os.path.exists("CREDENTIALS_PICKLE_FILE")):
        heading = "You're not supposed to be here >:D"
        message = "Psst. Authenticate yourself!"
        return templates.TemplateResponse("blank.html", {"request":request,"heading":heading,"message":message})

    return templates.TemplateResponse("keywords.html", {"request":request})

@router.get("/keywords/downloads")
async def download(request: Request):
    file_path = "youtuber_keyword_search.csv"
    return FileResponse(path=file_path, filename=file_path, media_type='text/csv')

async def websocket_get_keywords(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()

    video_keywords = None

    # this coroutine sends each pieace of data one by one through the websocket
    async def send_info(video_keywords: List[Tuple[Video,List[str]]],channel_names_ids: dict):
        for video,sponsors in video_keywords:
            sponsor = sponsors
            channel = channel_names_ids[video.channel_id]
            publish_date = str(video.date)
            views = video.views
            link = "youtube.com/watch?v=" + video.video_id
            await websocket.send_json({"sponsor":sponsor,"channel":channel,"date":publish_date,"views":views,"link":link})

    def save_results_csv(video_keywords: List[Tuple[Video,List[str]]],channel_names_ids: dict):
        with open("youtuber_keyword_search.csv", "w", encoding='utf-8') as file:
            writer = csv.writer(file)

            for video,sponsors in video_keywords:
                sponsor = sponsors
                channel = channel_names_ids[video.channel_id]
                publish_date = str(video.date)
                views = video.views
                link = "youtube.com/watch?v=" + video.video_id
                writer.writerow([sponsor,channel,publish_date,str(views),link])

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
            await send_info(video_keywords=subsection,channel_names_ids=channel_names_ids)
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
            await send_info(video_keywords=video_keywords[start:end],channel_names_ids=channel_names_ids)
        elif action == 'add_keyword':
            new_keyword = data['keyword']
            keywords.append(new_keyword)
            await websocket.send_json({"message":"appended new keyword " + new_keyword})
        elif action == 'search':
            video_keywords = search_keywords(keywords=keywords+russian_keywords,db=db)
            await websocket.send_json({"message":"got search"})

            page = 0
            max_page = math.floor(len(video_keywords)/10)

            channel_names_ids = get_channel_names_ids(db)
            save_results_csv(video_keywords=video_keywords,channel_names_ids=channel_names_ids)
            await websocket.send_json({"action":"clear"})
            await send_info(video_keywords=video_keywords[:10],channel_names_ids=channel_names_ids)
        else:
            await websocket.send_json({"message":"something went wrong"})