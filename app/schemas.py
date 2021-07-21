from pydantic import BaseModel 

class AddCreator(BaseModel):
    channel_name: str
    channel_id: str 
