from fastapi import FastAPI, Request, Depends 
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.routing import request_response
from routers import auth 
from routers import creators
from handlers.gui import *

from sqlalchemy.orm import Session
from db.database import get_db

app = FastAPI()
app.include_router(auth.router)
app.include_router(creators.router)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = "POOPY"
    return templates.TemplateResponse("page.html", {"request": request, "data": data})


#----------------------- TO DELETE!!!!! --------------------------------------------

@app.get("/DEL")
async def delete(request: Request, channel_name: str, db: Session = Depends(get_db)):
    
    try:
        db.execute("DELETE FROM creators WHERE channel_name='%s'"%channel_name)
        db.commit()
        message = "Success!"
    except Exception as e:
        message = "FAILED: " + str(e)

    return {"message":message}

@app.get("/getTop")
def get_top(table:str, limit: int, db: Session = Depends(get_db)):
    try:
        rows = []
        results = db.execute("SELECT * FROM " + table + " LIMIT " + str(limit))
        for row in results:
            rows.append(row)
        return {"rows":rows}
    except Exception as e:
        return {"error":str(e)}
