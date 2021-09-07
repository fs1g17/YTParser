# Handlers imports
from handlers.authentication import is_auth

# Database imports   
from db.database import get_db      
from db.database import Creator

# SQLAlchemy imports 
from sqlalchemy import text 
from sqlalchemy.orm import Session

# FastAPI imports
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request, APIRouter, Depends

router = APIRouter()
templates = Jinja2Templates(directory="templates")

error_messages = ["Creator already in the database","YouTube can not find given channel","Please authenticate yourself first"]

# --------------- TODO: implement adding a creator functionality!!!
@router.get("/viewCreators", response_class=HTMLResponse)
async def view_creators(request: Request, db: Session = Depends(get_db), page: int = 0, message: str = ""):
    authenticated = is_auth()
    if not(authenticated):
        heading = "Not authorised."
        message = "Please authorise first!"
        return templates.TemplateResponse("blank.html", {"request":request,"heading":heading,"message":message})

    start = page*10 + 1
    size = 10
    
    results = db.query(Creator).filter(text("id >= %s AND id < %s"%(start,start+size)))
    ytbrs = []
    for creator in results:
        channel_name = creator.channel_name
        channel_id = creator.channel_id
        ytbrs.append([channel_name,channel_id])
    
    num_creators = db.query(Creator).count()
    return templates.TemplateResponse("view_creators.html", {"request":request,"ytbrs":ytbrs, "page":page, "num_creators":num_creators, "message":message})