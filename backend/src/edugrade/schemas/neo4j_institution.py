from pydantic import BaseModel
from typing import Optional

class InstitutionUpsertIn(BaseModel):
    mongoId: str
    name: str
    country: Optional[str] = None
    level: Optional[str] = None

class InstitutionOut(BaseModel):
    mongoId: str
    name: str
    country: Optional[str] = None
    level: Optional[str] = None
