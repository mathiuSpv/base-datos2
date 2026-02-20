from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict, field_validator
from edugrade.core.mongo_types import PyObjectId
from edugrade.utils.object_id import is_objectid_hex

class GradeCreate(BaseModel):
  id_subject: str
  id_student: str
  id_institution: str

  system: str = Field(min_length=1, max_length=50)
  name: str = Field(min_length=1, max_length=200)
  type: str = Field(min_length=1, max_length=50)
  date: date

  value: float

  @field_validator("id_subject", "id_student", "id_institution")
  @classmethod
  def validate_ids(cls, v: str):
    if not is_objectid_hex(v):
      raise ValueError("Must be a valid 24-char ObjectId hex string")
    return v

class GradeOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    id: PyObjectId = Field(alias="_id")

    id_subject: str
    id_student: str
    id_institution: str

    system: str
    name: str
    type: str
    date: date

    value: float
    value_converted: float | None = None

    createdAt: datetime
