from pydantic import BaseModel
from typing import Optional

class InstitutionUpsertIn(BaseModel):
    mongoId: str
    name: str
    country: Optional[str] = None
#    level: Optional[str] = None # para que diga Primaria/Secundaria etc (o poner type que está en mongodb)

class InstitutionOut(BaseModel):
    mongoId: str
    name: str
    country: Optional[str] = None
#    level: Optional[str] = None
