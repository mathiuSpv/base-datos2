from pydantic import BaseModel
from typing import Optional

class SubjectUpsertIn(BaseModel):
    mongoId: str
    name: str
    area: Optional[str] = None
    level: Optional[str] = None

class SubjectOut(BaseModel):
    mongoId: str
    name: str
    area: Optional[str] = None
    level: Optional[str] = None
