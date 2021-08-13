import os
from handlers.YTHandler import *
from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

router = APIRouter()

@router.get("/authorise", response_class=HTMLResponse)
async def auth_start(request: Request):
    if os.path.exists("CREDENTIALS_PICKLE_FILE"):
        return templates.TemplateResponse("auth_done.html", {"request":request})
    
    link,_ = get_auth_service_link()
    link = link[0]
    return templates.TemplateResponse("auth.html", {"request":request, "link":link})

@router.get("/authorise/code", response_class=HTMLResponse)
async def disp_auth_code(code: str, request: Request):
    try:
        _,flow = get_auth_service_link()
        auth = get_credentials(flow,code)
        with open("CREDENTIALS_PICKLE_FILE", 'wb') as f:
            pickle.dump(auth, f)
        return templates.TemplateResponse("auth_done.html", {"request":request, "code":code})
    except:
        return templates.TemplateResponse("auth_fail.html", {"request":request})