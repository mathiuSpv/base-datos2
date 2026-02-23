from fastapi import HTTPException
from edugrade.repository.mongo.options import OptionsRepository

class OptionsService:
  def __init__(self, db):
    self.repo = OptionsRepository(db)

  async def get_option(self, key: str, only_values: bool = False):
    doc = await self.repo.get_by_key(key)
    if not doc:
      raise HTTPException(status_code=404, detail="Option not found")

    if not only_values:
      return doc
    
    if "values" in doc:
      return doc["values"]

    if "response" in doc:
      return doc["response"]

    raise HTTPException(status_code=404, detail="No values found for this option")