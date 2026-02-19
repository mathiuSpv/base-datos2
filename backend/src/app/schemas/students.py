from pydantic import BaseModel
from typing import Optional

class StudentUpsertIn(BaseModel):
    mongoId: str
    fullName: str
    country: Optional[str] = None

class StudentOut(BaseModel):
    mongoId: str
    fullName: str
    country: Optional[str] = None
