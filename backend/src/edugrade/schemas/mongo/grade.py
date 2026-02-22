from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict, field_validator
from edugrade.core.mongo_types import PyObjectId
from edugrade.utils.object_id import is_objectid_hex

class GradeCreate(BaseModel):
  subjectId: str
  studentId: str
  institutionId: str

  name: str = Field(min_length=1, max_length=200)
  system: str = Field(min_length=1, max_length=50)
  type: str = Field(min_length=1, max_length=50)
  country: str = Field(min_length=2, max_length=80)
  grade: str = Field(min_length=1, max_length=50)

  date: date
  value: str = Field(min_length=1, max_length=50)

  @field_validator("subjectId", "studentId", "institutionId")
  @classmethod
  def validate_ids(cls, v: str):
    if not is_objectid_hex(v):
      raise ValueError("Must be a valid 24-char ObjectId hex string")
    return v

class GradeOut(BaseModel):
  model_config = ConfigDict(
    populate_by_name=True,
    arbitrary_types_allowed=True
    )
  id: PyObjectId = Field(alias="_id")

  subjectId: str
  studentId: str
  institutionId: str

  system: str
  name: str
  type: str
  date: date
  country: str
  grade: str

  value: str
  valueConverted: str | None = None

  createdAt: datetime
