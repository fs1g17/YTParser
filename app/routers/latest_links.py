import csv
import enum
import json
from logging import log

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

# async def websocket_get_links(websocket: WebSocket, db: Session = Depends(get_db)):
#     await websocket.accept()

#     await websocket.send_text(str({"message":"connected"}))
#     while True:
#         receive_message = await websocket.receive_text()
#         await websocket.send_text(str({"message":"fuck you"}))


async def websocket_get_links(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    print("connected")

    await websocket.send_text(str({"message":"connected"}))

    #data = db.execute("SELECT * FROM creators LIMIT 100;")
    data = db.execute("SELECT * FROM creators;")


    # start = 100
    # end = 110
    # query = "SELECT * FROM ( SELECT creators.*, ROW_NUMBER () OVER () as rnum FROM creators ) x WHERE rnum BETWEEN %s AND %s;"%(start,end)
    # data = db.execute(query)
    await websocket.send_text(str({"message":"executed db query"}))
    youtube = get_auth_service()
    await websocket.send_text(str({"message":"got youtube service"}))
    creators_links = []
    i=0

    with open("youtuber_latest_links.csv","w",encoding='utf-8',newline='') as file:
        mywriter = csv.writer(file)

        for row in data:
            
            i += 1

            channel_name = row[0]
            channel_id = row[1]
            current_message = "done: " + str(channel_name)
            await websocket.send_text(str({"message":current_message}))
            try:
                links = get_latest_links(channel_id,youtube)

                link_string = "\n".join([x.rstrip() for x in links])
                mywriter.writerow([channel_name.rstrip(),link_string.rstrip()])

                for i in range(len(links)):
                    if i==0:
                        creators_links.append([channel_name,links[i]])
                        continue
                    
                    creators_links.append([" ",links[i]])
            except Exception as e:
                print("ERROR: " + str(e))
                await websocket.send_text(str({"message":str(e)}))


    total_num_rows = len(creators_links)
    
    page = 0
    row_limit = 10 
    last_creator = " "

    while True:
        receive_message = await websocket.receive_text()
        if(receive_message == "next"):
            if page*row_limit < total_num_rows: 
                page += 1
        if(receive_message == "prev"):
            page -= 1
            if page < 0:
                page = 0

        #TODO: what if I only load in 10 users at a time? allbeit aat the cost of
        start = page*row_limit
        end = start + row_limit 
        if end > total_num_rows:
            end = total_num_rows + 1
        
        for i,row in enumerate(creators_links[start:end]):
            try:
                name = row[0]
                link = row[1]
                
                if name != " ":
                    last_creator = name

                if i==0:
                    name = last_creator
                
                await websocket.send_text(str({name:link}))
            except Exception as e:
                await websocket.send_text(str(e))