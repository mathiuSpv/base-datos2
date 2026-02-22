from bson import ObjectId
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic_core import core_schema

class PyObjectId(ObjectId):
  @classmethod
  def __get_pydantic_core_schema__(cls, source_type, handler: GetCoreSchemaHandler):
    def validate(v):
      if isinstance(v, ObjectId):
        return v
      if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
      raise ValueError("Invalid ObjectId")

    return core_schema.no_info_plain_validator_function(
      validate,
      serialization=core_schema.plain_serializer_function_ser_schema(lambda x: str(x)),
    )
  
  @classmethod
  def __get_pydantic_json_schema__(cls, _core_schema, handler: GetJsonSchemaHandler):
    json_schema = handler(core_schema.str_schema())
    json_schema.update(
      examples=["507f1f77bcf86cd799439011"],
      description="MongoDB ObjectId",
    )
    return json_schema
