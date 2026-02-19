from pydantic import BaseModel
from typing import Optional

class StudiesAtIn(BaseModel):
    studentId: str
    institutionId: str
    startDate: Optional[str] = None  # ISO string
    endDate: Optional[str] = None

class TookIn(BaseModel):
    studentId: str
    subjectId: str
    grade1: Optional[float] = None
    grade2: Optional[float] = None
    general: Optional[float] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None

class EquivalentToIn(BaseModel):
    fromSubjectId: str
    toSubjectId: str
    confidence: Optional[float] = 1.0
    source: Optional[str] = None
