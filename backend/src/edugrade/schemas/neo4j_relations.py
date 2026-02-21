from pydantic import BaseModel
from typing import Optional

''' S (Student) -> I (Institution) '''
# ambos id son de mongo, acá se usan como str

class StudiesAtIn(BaseModel):
    studentMongoId: str
    institutionMongoId: str
    startDate: Optional[str] = None  # ISO string, tipo "2018-03-01"
    endDate: Optional[str] = None # ISO string, SINO USAMOS ->  Optional[date] = None

''' S (Student) -> M (Subject) '''
# studentMongoId: de Mongo
# subjectNeoId: de Neo id internal (se maneja como string en la API)

class TookIn(BaseModel):
    studentMongoId: str
    subjectNeoId: str
    year: Optional[int] = None # Ejemplo: 2023
    grade: Optional[str] = None # Ejemplo: "S6" (Secundaria 6to)

#class EquivalentToIn(BaseModel):  # NO SE USA PORQUE NO ESTAMOS VIENDO EQUIVALENCIAS, SINO TRAYECTORIA ACADÉMICA
#    fromSubjectId: str
#    toSubjectId: str
#    confidence: Optional[float] = 1.0
#    source: Optional[str] = None
