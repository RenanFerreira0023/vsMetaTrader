from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    estagio0: Optional[str] = None
    estagio1: Optional[str] = None
    estagio2: Optional[str] = None
    estagio3: Optional[str] = None
    prompt: Optional[str] = None
    session_uuid: Optional[str] = None

class IndexRobotsRequest(BaseModel):
    path: str
