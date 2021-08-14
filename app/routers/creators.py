import os

from starlette.responses import RedirectResponse
from handlers.authentication import verify_cached_credentials
from handlers.YTHandler import verify_channel

# Database imports
from db.models import Creator
from db.database import get_db
from db.schemas import AddCreator                                                                      

# SQLAlchemy imports 
from sqlalchemy.orm import Session

# FastAPI imports
from fastapi.param_functions import Body 
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request, APIRouter, Depends

router = APIRouter()
templates = Jinja2Templates(directory="templates")

error_messages = ["Creator already in the database","YouTube can not find given channel","Please authenticate yourself first"]

@router.get("/viewCreators", response_class=HTMLResponse)
async def view_creators(request: Request, db: Session = Depends(get_db), page: int = 0, message: str = ""):
    cached = verify_cached_credentials()
    if not(cached):
        message = "Please authorise first!"
        return templates.TemplateResponse("view_creators_fail.html", {"request":request,"message":message})
    
    start = (page)*10 + 1
    end = start + 9
    query = "SELECT * FROM ( SELECT creators.*, ROW_NUMBER () OVER () as rnum FROM creators ) x WHERE rnum BETWEEN %s AND %s;"%(start,end)
    results = db.execute(query)
    ytbrs = []
    for i,row in enumerate(results):
        channel_name = row[0]
        channel_id = row[1]
        ytbrs.append([channel_name,channel_id])
    
    num_creators = db.execute("SELECT * FROM creators").rowcount
    return templates.TemplateResponse("view_creators.html", {"request":request,"ytbrs":ytbrs, "page":page, "num_creators":num_creators, "message":message})


@router.get("/addCreator", response_class=RedirectResponse)
def add_creator(ch_name: str, ch_id: str, request: Request, db: Session = Depends(get_db), page: int = 0):   
    channel_status = verify_channel(ch_id)

    if(channel_status == -1):
        message = error_messages[2]
    if(channel_status == 0):
        message = error_messages[1]
    
    if(channel_status < 1):
        return "/viewCreators?message=" + message

    try:
        if(len(ch_name) > 0 and len(ch_id) > 0):
            to_create = Creator (
                channel_name = ch_name,
                channel_id = ch_id
            )
            db.add(to_create)
            db.commit()
            message = ""
    except Exception as e:
        message = str(e)

        if "UniqueViolation" in message:
            message = error_messages[0]

    if message == "":
        return "/viewCreators"

    if page == 0:
        page_url_attribute = ""
    else:
        page_url_attribute = "&page=" + str(page)
    return "/viewCreators?message=" + message + page_url_attribute
        
#TODO: automatically navigate to the page with the newly added creator??
#TODO: regex the youtube channel_id to make sure that it actually works! <-- can't regex, maybe check with API?
#TODO: inside all the YouTube API handle functions, ensure that the channel_id actually works!
# query = "SELECT * FROM ( SELECT creators.*, ROW_NUMBER () OVER () as rnum FROM creators ) x WHERE rnum BETWEEN 10 AND 20;" <---- this works!!!!
#query2 = "SELECT * FROM (SELECT row_number() over(), * FROM creators) LIMIT 10"
#query3 = "SELECT * FROM creators LIMIT 10;"