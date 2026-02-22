from pydantic import BaseModel, Field
from typing import Optional

class SubjectUpsertIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    institutionMongoId: str  # de Mongo

class SubjectOut(BaseModel):
    id: str # uuid (Subject.id)
    name: str
    institutionMongoId: str

