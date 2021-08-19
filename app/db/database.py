from sqlalchemy import create_engine
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import session, sessionmaker, subqueryload_all
from sqlalchemy.sql.expression import table
from sqlalchemy.sql.schema import Column
from sqlalchemy_utils import create_database, database_exists
import databases
from sqlalchemy.dialects import postgresql
from pydantic import BaseModel


#conn_url = 'postgresql+psycopg2://yourUserDBName:yourUserDBPassword@yourDBDockerContainerName/yourDBName'


DB_URL = "postgresql://postgres:root@YTParser_postgres/youtube"

database = databases.Database(DB_URL)
metadata = sqlalchemy.MetaData()

creators = sqlalchemy.Table(
    "creators",
    metadata,
    Column("channel_name", sqlalchemy.TEXT, primary_key=True),
    Column("channel_id", sqlalchemy.TEXT)
)

videos = sqlalchemy.Table(
    "videos",
    metadata,
    Column("channel_id", postgresql.TEXT, primary_key=True),
    Column("video_id", postgresql.TEXT, primary_key=True),
    Column("video_info",postgresql.TEXT)
)

engine = sqlalchemy.create_engine(DB_URL)
metadata.create_all(engine)

class Creator(BaseModel):
    channel_name: str
    channel_id: str

class Video(BaseModel):
    channel_id: str
    video_id: str
    video_info: str

sesh = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = sesh()
    try:
        yield db
    except:
        db.close()
    finally:
        db.close()

def validate_database():
    if not database_exists(engine.url):
        create_database(engine.url)

#--------------OLD
# DB_URL = "postgresql+psycopg2://postgres:root@YTParser_postgres/youtube"

# engine = create_engine(DB_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     except:
#         db.close()
#     finally:
#         db.close()

# def validate_database():
#     if not database_exists(engine.url):
#         create_database(engine.url)
