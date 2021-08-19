import json
from logging import log
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
    return templates.TemplateResponse("latest_links.html", {"request":request})


async def websocket_get_links(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    print("connected")

    data = db.execute("SELECT * FROM creators LIMIT 10;")
    youtube = get_auth_service()
    creators_links = []

    for row in data:
        channel_name = row[0]
        channel_id = row[1]
        links = get_latest_links(channel_id,youtube)

        for i in range(len(links)):
            if i==0:
                creators_links.append([channel_name,links[i]])
                continue
            
            creators_links.append([" ",links[i]])

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

    # while True:
    #     receive_message = await websocket.receive_text()
    #     if(receive_message == "next"):
    #         if page*row_limit < total_num_rows: 
    #             page += 1
    #     if(receive_message == "prev"):
    #         page -= 1
    #         if page < 0:
    #             page = 0

    #     start = page*row_limit
    #     end = start + row_limit 

    #     if(end > total_num_rows):
    #         #[k : creators_links[k] for k in list(creators_links)[start:]]
    #         vals_to_send = creators_links[start:]
    #     else:
    #         #vals_to_send = {k : creators_links[k] for k in list(creators_links)[start:end]}
    #         vals_to_send = creators_links[start:end]
    #     try:
    #         await websocket.send_text(str(vals_to_send))
    #     except Exception as e:
    #         await websocket.send_text(str(e))

# async def websocket_get_links(websocket: WebSocket, db: Session = Depends(get_db)):
#     await websocket.accept()
#     print("connected")

#     data = db.execute("SELECT * FROM creators LIMIT 10;")
#     youtube = get_auth_service()
#     creators_links = {}

#     total_num_rows = 0
#     for row in data:
#         channel_name = row[0]
#         channel_id = row[1]
#         links = get_latest_links(channel_id,youtube)
#         creators_links[channel_name] = links
#         total_num_rows += len(links)

    
#     page = 0
#     row_limit = 10 

#     while True:
#         receive_message = await websocket.receive_text()
#         if(receive_message == "next"):
#             if page*row_limit < total_num_rows: 
#                 page += 1
#         if(receive_message == "prev"):
#             page -= 1
#             if page < 0:
#                 page = 0

#         start = page*row_limit
#         end = start + row_limit 

#         if(end > total_num_rows):
#             vals_to_send = {k : creators_links[k] for k in list(creators_links)[start:]}
#         else:
#             vals_to_send = {k : creators_links[k] for k in list(creators_links)[start:end]}

#         try:
#             await websocket.send_text(str(vals_to_send))
#         except Exception as e:
#             await websocket.send_text(str(e))