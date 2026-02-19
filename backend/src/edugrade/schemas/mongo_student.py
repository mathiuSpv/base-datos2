from datetime import date
from pydantic import BaseModel, Field, ConfigDict
from edugrade.core.mongo_types import PyObjectId

class StudentCreate(BaseModel):
  identity: str | None = Field(default=None, min_length=3, max_length=20)
  firstName: str = Field(min_length=1, max_length=100)
  lastName: str = Field(min_length=1, max_length=100)
  birthDate: date
  nationality: str = Field(min_length=2, max_length=80)

class StudentOut(BaseModel):
  model_config = ConfigDict(
    populate_by_name=True,
    arbitrary_types_allowed=True
    )
  id: PyObjectId = Field(alias="_id")
  identity: str | None = None
  firstName: str
  lastName: str
  birthDate: date
  nationality: str