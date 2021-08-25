import os
import json
from starlette.websockets import WebSocket
from handlers.YTHandler import *
from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from db.database import get_db

templates = Jinja2Templates(directory="templates")

router = APIRouter()

@router.get("/keywords", response_class=HTMLResponse)
async def keywords(request: Request):
    if not(os.path.exists("CREDENTIALS_PICKLE_FILE")):
        heading = "You're not supposed to be here >:D"
        message = "Psst. Authenticate yourself!"
        return templates.TemplateResponse("blank.html", {"request":request,"heading":heading,"message":message})

    return templates.TemplateResponse("keywords.html", {"request":request})

async def websocket_get_keywords(websocket: WebSocket, db: Session = Depends(get_db)):
    # Accept connection
    await websocket.accept()

    # Receive "ready" message from client
    await websocket.receive_text()

    # Send over the first page of cached videos from DB 
    query = "SELECT * FROM videos LIMIT 10;"
    results = db.execute(query) 
    import ast 
    import json 
    for row in results:
        channel_id = row[0]
        video_info = row[2]

        video_info = ast.literal_eval(row[2])

        # video_info = str(video_info)
        # video_info = video_info.replace("\"","")
        # video_info = video_info.replace("\n"," ")
        # video_info = ast.literal_eval(video_info)

        date = video_info['date']
        views = video_info['views']
        description = video_info['description']
        description = description.replace("\n"," ")

        links = get_links(description)
        filtered_links = filter_links(links)
        
        print("VIDEO: " + str(video_info))

        await websocket.send_text(str({"channel":channel_id,"video_info":str(description)}))

    # Enter while loop 
    while True:
        receive_message = await websocket.receive_text()
        await websocket.send_text(str({"message":str(receive_message)}))




async def websocket_get_keywords3(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()

    row_limit = 10 
    total_num_rows = 150

    while True:
        # data = await websocket.receive_text()
        # await websocket.send_text(str({"message":data}))
        receive_message = await websocket.receive_text()

        if(receive_message == "next"):
            if total_num_rows == 0:
                total_num_rows = db.execute("SELECT * FROM videos;").rowcount

            if page*row_limit <= total_num_rows: 
                page += 1
        if(receive_message == "prev"):
            page -= 1
            if page < 0:
                page = 0

        start = page*row_limit
        end = start + row_limit 
        if end > total_num_rows:
            end = total_num_rows + 1

        query = "SELECT * FROM ( SELECT video.*, ROW_NUMBER () OVER () as rnum FROM videos ) x WHERE rnum BETWEEN %s AND %s;"%(start,end)
        results = db.execute(query)

        for row in results:
            channel_id = row[0]
            video_id = row[1]
            video_info = row[2]
            #channel_name = creators_names[channel_id]

            await websocket.send_text(str({"channel":channel_id,"video_info":video_info}))

async def websocket_get_keywords2(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    print("accepted!")
    await websocket.send_text(str({"message":"connected"}))

    results = db.execute("SELECT * FROM creators;")
    await websocket.send_text(str({"message":"looking through creators"}))
    creators_names = {}
    for row in results:
        creators_names[row[1]] = row[0]

    print("got all creators")
    await websocket.send_text(str({"message":"got all creators"}))

    page = 0
    row_limit = 10 
    total_num_rows = db.execute("SELECT * FROM videos;").rowcount

    print("waiting for message")

    await websocket.send_text(str({"message":"READY"}))

    while True:
        receive_message = await websocket.receive_text()
        if(receive_message == "next"):
            if page*row_limit <= total_num_rows: 
                page += 1
        if(receive_message == "prev"):
            page -= 1
            if page < 0:
                page = 0

        start = page*row_limit
        end = start + row_limit 
        if end > total_num_rows:
            end = total_num_rows + 1

        query = "SELECT * FROM ( SELECT video.*, ROW_NUMBER () OVER () as rnum FROM videos ) x WHERE rnum BETWEEN %s AND %s;"%(start,end)
        results = db.execute(query)

        for row in results:
            channel_id = row[0]
            video_id = row[1]
            video_info = row[2]
            channel_name = creators_names[channel_id]

            websocket.send_text(str({"channel":channel_id,"video_info":video_info}))

