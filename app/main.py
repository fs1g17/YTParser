from routers import auth 
from routers import latest_links
from routers import keyword_search
from routers import creators as youtubers

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import desc

from db.database import get_db, Creator, Video
from handlers.authentication import get_auth_service
from handlers.DBHandler import get_creators_range, cache_range, get_channel_names_ids, update_db_channel

# import alembic.config
# alembicArgs = [
#     '--raiseerr',
#     'upgrade', 'head'
# ]
# alembic.config.main(argv=alembicArgs)

app = FastAPI()
app.include_router(auth.router)
app.include_router(youtubers.router)
app.include_router(latest_links.router)
app.include_router(keyword_search.router)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = "POOPY"
    return templates.TemplateResponse("home_page.html", {"request": request, "data": data})

app.add_api_websocket_route("/latestLinks/ws", latest_links.websocket_get_links)
app.add_api_websocket_route("/keywords/ws", keyword_search.websocket_get_keywords)

@app.get("/updateCreator")
def update_creator(channel_id: str, db: Session = Depends(get_db)):
    try:
        youtube = get_auth_service()
        messages = update_db_channel(db=db,channel_id=channel_id,youtube=youtube)
        return {"success!":messages}
    except Exception as e:
        return {"failure":str(e)}

@app.get("/nothing")
def nothing():
    return {"nothing":True}

@app.get("/getUniqueCreatorsVideos")
def get_uniq_creators_vids(db: Session = Depends(get_db)):
    try:
        results = db.execute("SELECT DISTINCT channel_id FROM videos;")
        ch_ids = []
        for row in results:
            ch_ids.append(row[0])

        name = []
        for channel_id in ch_ids:
            result = db.query(Creator).filter(Creator.channel_id == channel_id)
            for row in result:
                name.append(row)

        return {"success!":name}
    except Exception as e:
        return {"failed":str(e)}

@app.get("/cacheRange")
def cache_test(start: int, size: int, db: Session = Depends(get_db)):
    try:
        messages = cache_range(start=start,size=size,db=db)
        return {"success!":messages}
    except Exception as main_exception:
        return {"failure in main":str(main_exception)}

#TODO: it looks like the app is skipping click on car "62" completely!
@app.get("/checkRange")
def cache_check(start: int, size: int, db: Session = Depends(get_db)):
    try:
        creators = get_creators_range(start=start,size=size,db=db)
        done = []
        for creator in creators:
            channel_name = creator.channel_name
            id = creator.id
            done.append([id,channel_name])
        return {"success!":str(done)}
    except Exception as e:
        return {"Main: failed ":str(e)}

@app.get("/showCreators")
def show_creators(start:int = 1, limit: int = 230, db: Session = Depends(get_db)):
    try:
        results = db.query(Creator).offset(start).limit(limit).all()
        rows = []

        for creator in results:
            rows.append([creator.id,creator.channel_name,creator.channel_id])
        
        return {"success":rows}
    except Exception as e:
        return {"failure":str(e)}

@app.get("/showVideos")
def show_videos(start:int = 1, limit: int = 230, db: Session = Depends(get_db)):
    try:
        results = db.query(Video).order_by(desc(Video.date)).offset(start).limit(limit).all()
        rows = []

        for video in results:
            rows.append([video.date,video.channel_id])
        
        return {"success":rows}
    except Exception as e:
        return {"failure":str(e)}  

@app.get("/getDateRanges")
def get_date_ranges(db: Session = Depends(get_db)):
    try:
        all_vids = db.query(Video).order_by(desc(Video.date)).all()
        date_ranges = {}

        for video in all_vids:
            channel = video.channel_id
            video_date = video.date
            
            if not(channel in date_ranges):
                date_ranges[channel] = {"start":video_date,"end":video_date}
                continue 

            date_range = date_ranges[channel]
            start = date_range['start']
            end = date_range['end']

            if video_date < start:
                date_range['start'] = video_date 
                continue 

            if video_date > end:
                date_range['end'] = video_date
        
        return {"success":date_ranges}
    except Exception as e:
        return {"failure":str(e)}

@app.get("/num_vids")
def get_info(db: Session = Depends(get_db)):
    try:
        channel_names_ids = get_channel_names_ids(db=db)
        all_vids = db.query(Video).order_by(desc(Video.date)).all()
        date_ranges = {}
        num_vids = {}

        for video in all_vids:
            channel_id = video.channel_id
            channel = channel_names_ids[channel_id]
            video_date = video.date
            
            if not(channel in date_ranges):
                date_ranges[channel] = {"start":video_date,"end":video_date}
            else:
                date_range = date_ranges[channel]
                start = date_range['start']
                end = date_range['end']

                if video_date < start:
                    date_range['start'] = video_date 
                elif video_date > end:
                    date_range['end'] = video_date

            if not(channel in num_vids):
                num_vids[channel] = 1
            else:
                num_vids[channel] += 1
        return {"date_range":date_ranges,"num_vids":num_vids}
    except Exception as e:
        return {"failure":str(e)}
