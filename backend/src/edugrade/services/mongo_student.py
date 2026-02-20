from bson import ObjectId
from fastapi import HTTPException
from edugrade.repository.mongo_student import StudentRepository

class StudentService:
  def __init__(self, db):
    self.repo = StudentRepository(db)

  async def bootstrap(self) -> None:
    await self.repo.ensure_indexes()

  async def create(self, payload: dict) -> dict:
    return await self.repo.create(payload)

  async def get(self, student_id: str) -> dict:
    if not ObjectId.is_valid(student_id):
      raise HTTPException(status_code=400, detail="Invalid id")

    doc = await self.repo.get_by_id(ObjectId(student_id))
    if not doc:
      raise HTTPException(status_code=404, detail="Student not found")
    return doc

  async def list(
    self,
    first_name: str | None,
    last_name: str | None,
    nationality: str | None,
    identity: str | None,
    limit: int,
    skip: int,
  ) -> list[dict]:
    if identity and not nationality:
      raise HTTPException(status_code=400, detail="Nationality is required when identity is provided")

    return await self.repo.list(
      first_name=first_name,
      last_name_like=last_name,
      nationality=nationality,
      identity=identity,
      limit=limit,
      skip=skip,
    )

  async def delete(self, student_id: str) -> None:
    if not ObjectId.is_valid(student_id):
      raise HTTPException(status_code=400, detail="Invalid id")

    ok = await self.repo.delete(ObjectId(student_id))
    if not ok:
      raise HTTPException(status_code=404, detail="Student not found")