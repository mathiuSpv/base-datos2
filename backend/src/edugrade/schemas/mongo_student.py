from datetime import date
from pydantic import BaseModel, Field
from edugrade.core.mongo_types import PyObjectId

class StudentCreate(BaseModel):
  firstName: str = Field(min_length=1, max_length=100)
  lastName: str = Field(min_length=1, max_length=100)
  birthDate: date
  nationality: str = Field(min_length=2, max_length=80)

class StudentOut(BaseModel):
  id: PyObjectId = Field(alias="_id")
  firstName: str
  lastName: str
  birthDate: date
  nationality: str

  class Config:
    populate_by_name = True
