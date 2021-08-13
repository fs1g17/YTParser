from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

router = APIRouter()

@router.get("/authorise", response_class=HTMLResponse)
async def auth_start(request: Request):
    link = "https://www.google.com/poop/"
    return templates.TemplateResponse("auth.html", {"request":request, "link":link})

@router.get("/authorise/code", response_class=HTMLResponse)
async def disp_auth_code(code: str, request: Request):
    return templates.TemplateResponse("auth_done.html", {"request":request, "code":code})