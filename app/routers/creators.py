import os
from handlers.authentication import verify_cached_credentials
from db.database import get_db
from sqlalchemy.orm import Session
from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

router = APIRouter()

@router.get("/viewCreators", response_class=HTMLResponse)
async def auth_start(request: Request, db: Session = Depends(get_db), page: int = 0):
    cached = verify_cached_credentials()
    if not(cached):
        message = "Please authorise first!"
        return templates.TemplateResponse("view_creators_fail.html", {"request":request,"message":message})
    
    start = (page)*10 + 1
    end = start + 9
    query = "SELECT * FROM ( SELECT creators.*, ROW_NUMBER () OVER () as rnum FROM creators ) x WHERE rnum BETWEEN %s AND %s;"%(start,end)
    #query2 = "SELECT * FROM (SELECT row_number() over(), * FROM creators) LIMIT 10"
    #query3 = "SELECT * FROM creators LIMIT 10;"
    results = db.execute(query)
    ytbrs = []
    for i,row in enumerate(results):
        channel_name = row[0]
        channel_id = row[1]
        ytbrs.append([channel_name,channel_id])
    return templates.TemplateResponse("view_creators.html", {"request":request,"ytbrs":ytbrs})


# query = "SELECT * FROM ( SELECT creators.*, ROW_NUMBER () OVER () as rnum FROM creators ) x WHERE rnum BETWEEN 10 AND 20;" <---- this works!!!!