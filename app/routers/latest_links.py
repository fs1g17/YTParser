import csv
import math
from logging import log
from typing import List, Tuple

from starlette.responses import FileResponse
from handlers.DBHandler import get_creators
from handlers.YTHandler import verify_channel, get_latest_links
from handlers.authentication import verify_cached_credentials, get_auth_service

# Database imports
# from db.models import Creator
# from db.database import get_db, validate_database
# from db.schemas import AddCreator                                                                      
from db.database import Creator, Video 
from db.database import get_db, validate_database

# SQLAlchemy imports 
from sqlalchemy.orm import Session

# FastAPI imports
from fastapi.param_functions import Body 
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request, APIRouter, Depends, WebSocket


templates = Jinja2Templates(directory="templates")

router = APIRouter()

@router.get("/latestLinks", response_class=HTMLResponse)
async def disp_auth_code(request: Request):
    cached = verify_cached_credentials()
    if not(cached):
        heading = "Access Denied!"
        message = "Please authorise first!"
        return templates.TemplateResponse("blank.html", {"request":request,"heading":heading,"message":message})

    return templates.TemplateResponse("latest_links.html", {"request":request})


@router.get("/latestLinks/downloads")
async def download(request: Request):    
    file_path = "youtuber_latest_links.csv"
    return FileResponse(path=file_path, filename=file_path, media_type='text/csv')

async def websocket_get_links(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()

    youtube = get_auth_service()
    creators_links = {}
    rows = []
    for creator in db.query(Creator).all():
        channel_id = creator.channel_id
        channel_name = creator.channel_name

        try:
            links = get_latest_links(channel_id,youtube)
            creators_links[channel_name] = links

            for i,link in enumerate(links):
                if i==0:
                    rows.append((channel_name,link))
                    continue
                rows.append((" ",link))

        except Exception as e:
            await websocket.send_json({"message":str(e)})

    with open("youtuber_latest_links.csv", "w", encoding='utf-8') as file:
        writer = csv.writer(file)
        for creator,links in creators_links.items():
            link_string = "\n".join([x.rstrip() for x in links])
            writer.writerow([creator.rstrip(),link_string.rstrip()])

    total_num_rows = len(rows)
    curr_page = 0 
    rows_on_page = 10
    max_page = math.floor(total_num_rows/10)

    async def send_page(page: int):
        start = page*rows_on_page
        end = start + rows_on_page
        rows_subset = rows[start:end]

        for row in rows_subset:
            channel_name = row[0]
            link = row[1]
            await websocket.send_json({"channel_name":channel_name,"link":link})
    
    async def clear_table():
        await websocket.send_json({"action":"clear"})

    await send_page(curr_page)
    while True:
        received_message = await websocket.receive_json()

        action = received_message['action']
        if action == 'next':
            if curr_page == max_page:
                continue 
            curr_page += 1
        elif action == 'prev':
            if curr_page == 0:
                continue 
            curr_page -= 1
        
        await clear_table()
        await send_page(curr_page)
