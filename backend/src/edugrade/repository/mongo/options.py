class OptionsRepository:
  def __init__(self, db):
      self.col = db["options"]

  async def ensure_indexes(self) -> None:
    await self.col.create_index("key", unique=True)

  async def get_by_key(self, key: str) -> dict | None:
    return await self.col.find_one({"key": key})

  async def get_grade_map(self) -> dict[str, int] | None:
    doc = await self.get_by_key("grade")
    if not doc:
      return None
    values = doc.get("values")
    return values if isinstance(values, dict) else None
  
  async def get_countries(self) -> list[str] | None:
    doc = await self.get_by_key("countries")
    if not doc:
      return None
    values = doc.get("values")
    return values if isinstance(values, list) else None