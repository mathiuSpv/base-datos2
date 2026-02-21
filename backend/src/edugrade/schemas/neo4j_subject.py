from pydantic import BaseModel, Field
from typing import Optional

class SubjectUpsertIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
#    area: Optional[str] = None si se quiere poner algo como matemática, ciencias, lenguaje


class SubjectOut(BaseModel):
    id: str  # Neo4j id (devuelve string)
    name: str
#    area: Optional[str] = None
