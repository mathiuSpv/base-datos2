from pydantic import BaseModel, Field, ConfigDict
from edugrade.core.mongo_types import PyObjectId

class InstitutionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    country: str = Field(min_length=2, max_length=80)
    type: str = Field(min_length=2, max_length=50)
    address: str = Field(min_length=1, max_length=250)

class InstitutionOut(BaseModel):
    model_config = ConfigDict(
      populate_by_name=True,
      arbitrary_types_allowed=True
    )

    id: PyObjectId = Field(alias="_id")
    name: str
    country: str
    type: str
    address: str