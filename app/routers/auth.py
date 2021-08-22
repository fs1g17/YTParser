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
        return templates.TemplateResponse("blank.html", {"request":request,"heading":"Authentication Complete","message":"You are already authenticated!"})
    
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
        heading = "Authorisation complete!"
        message = "You authenticated yourself successfully."
    except Exception as e:
        heading = "Authorisation failed!"
        message = "Error: " + str(e)
    return templates.TemplateResponse("blank.html", {"request":request,"heading":heading,"message":message})