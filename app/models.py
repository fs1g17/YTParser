from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.schema import Column
from database import Base 

class Creator(Base):
    __tablename__ = 'creators'
    channel_name = Column(postgresql.TEXT, primary_key=True)
    channel_id = Column(postgresql.TEXT)