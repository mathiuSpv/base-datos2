from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class DashboardOut(BaseModel):
  country: str = Field(min_length=3, max_length=3)
  institutionId: Optional[str] = None
  examsRead: int = 0
  examsUsedInAverage: int = 0

  averageZA: Optional[float] = None
  displayValue: Optional[str] = None
  displaySystem: Optional[str] = None


class SubjectAverageOut(BaseModel):
  subjectId: str
  subjectName: Optional[str] = None
  examsRead: int = 0
  examsUsedInAverage: int = 0
  averageZA: Optional[float] = None
  displayValue: Optional[str] = None
  displaySystem: Optional[str] = None


class DashboardSubjectsOut(BaseModel):
  country: str = Field(min_length=3, max_length=3)
  institutionId: str
  subjects: list[SubjectAverageOut] = Field(default_factory=list)