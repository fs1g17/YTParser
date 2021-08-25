from sqlalchemy import create_engine, Sequence
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import session, sessionmaker, subqueryload_all

from sqlalchemy.sql.expression import table
from sqlalchemy.sql.schema import Column
from sqlalchemy_utils import create_database, database_exists
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa

DB_URL = "postgresql+psycopg2://postgres:root@YTParser_postgres/youtube"
engine = create_engine(DB_URL)

Base = declarative_base()

class Creator(Base):
    __tablename__ = 'creators'
    id = Column(postgresql.INTEGER, primary_key=True)
    channel_name = Column(postgresql.TEXT, primary_key=True)
    channel_id = Column(postgresql.TEXT, nullable=False)

class Video(Base):
    __tablename__ = 'videos'
    channel_id = Column(postgresql.TEXT, primary_key=True)
    video_id = Column(postgresql.TEXT, primary_key=True)
    date = Column(postgresql.DATE)
    views = Column(postgresql.INTEGER)
    description = Column(postgresql.TEXT)
    
sesh = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#Base.metadata.create_all(engine)

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