from datetime import date
from pydantic import BaseModel, Field, ConfigDict, field_validator
from edugrade.core.mongo_types import PyObjectId
from edugrade.utils.string import non_empty_str

class ConversionRuleCreate(BaseModel):
    system: str = Field(min_length=1, max_length=50)
    country: str = Field(min_length=2, max_length=80)
    grade: str = Field(min_length=1, max_length=10)

    validFrom: date
    validTo: date | None = None

    map: dict[str, str]

    @field_validator("system", "country", "grade")
    @classmethod
    def _strip_fields(cls, v: str):
        return non_empty_str(v)

    @field_validator("map")
    @classmethod
    def _validate_map(cls, v: dict[str, str]):
        if not v:
            raise ValueError("map must not be empty")
        for k in v.keys():
            non_empty_str(k)
        for v in v.values():
            non_empty_str(v)
        return v


class ConversionRuleOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: PyObjectId = Field(alias="_id")
    system: str
    country: str
    grade: str
    validFrom: date
    validTo: date | None = None
    map: dict[str, str]