from __future__ import annotations
from typing import Optional
from edugrade.schemas.mongo.grade import GradeOut

class GradeOutDisplay(GradeOut):
  displayValue: Optional[str] = None
  displaySystem: Optional[str] = None