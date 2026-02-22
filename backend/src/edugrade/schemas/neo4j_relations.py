from pydantic import BaseModel
from typing import Optional

''' S (Student) -> I (Institution) '''
# ambos id son de mongo, acá se usan como str

class StudiesAtIn(BaseModel):
    studentMongoId: str
    institutionMongoId: str
    startDate: str # ISO string, tipo "2018-03-01"
    endDate: Optional[str] = None # ISO string, SINO USAMOS ->  Optional[date] = None

''' S (Student) -> M (Subject) '''
# studentMongoId: de Mongo
# subjectNeoId: de Neo id internal (se maneja como string en la API)

class TookIn(BaseModel):
    studentMongoId: str
    subjectId: str # antes era subjectNeoId
    year: int # Ejemplo: 2023
    grade: str # Ejemplo: "S6" (Secundaria 6to) | quitar optional | grade se trae del front

class EquivalentToIn(BaseModel):
    fromSubjectId: str   # UUID (Subject.id)
    toSubjectId: str     # UUID (Subject.id)
    levelStage: str         # ej "19"    

class EquivalentRemoveIn(BaseModel):
    subjectId: str
    levelStage: str  # "19"

#class EquivalentTo(BaseModel):  # NO SE USA PORQUE NO ESTAMOS VIENDO EQUIVALENCIAS, SINO TRAYECTORIA ACADÉMICA
#    fromSubjectId: str
#    toSubjectId: str
#    confidence: Optional[float] = 1.0
#    source: Optional[str] = None
#    endpoint de generar correlatividad de alta y baja de correlatividad


# endpoint, lo que se debe hacer es las call de los service, pero sin aplicar lógica
