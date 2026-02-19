from bson import ObjectId
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

class PyObjectId(ObjectId):
  @classmethod
  def __get_pydantic_core_schema__(cls, source_type, handler: GetCoreSchemaHandler):
    # Acepta str -> ObjectId y serializa ObjectId -> str
    def validate(v):
      if isinstance(v, ObjectId):
        return v
      if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
      raise ValueError("Invalid ObjectId")

    return core_schema.no_info_after_validator_function(
        validate,
        core_schema.str_schema(),
        serialization=core_schema.plain_serializer_function_ser_schema(lambda x: str(x)),
    )