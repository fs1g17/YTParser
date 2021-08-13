import sqlalchemy
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.schema import Column
from sqlalchemy.ext.declarative import declarative_base
#from database import Base 

Base = declarative_base()

class Creator(Base):
    __tablename__ = 'creators'
    channel_name = Column(postgresql.TEXT, primary_key=True)
    channel_id = Column(postgresql.TEXT)

class Video(Base):
    __tablename__ = 'videos'
    channel_id = Column(postgresql.TEXT, primary_key=True)
    video_id = Column(postgresql.TEXT, primary_key=True)
    video_info = Column(postgresql.TEXT)

class Keyword(Base):
    __tablename__ = 'keywords'
    video_info = Column(postgresql.TEXT, primary_key=True)
    keyword =Column(postgresql.TEXT, primary_key=True)