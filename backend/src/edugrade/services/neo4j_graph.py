from edugrade.core.neo4j_db import get_neo4j_driver
from edugrade.repository.neo4j_graph import Neo4jGraphRepository


class Neo4jGraphService:
    def __init__(self):
        self.driver = get_neo4j_driver()
        self.repo = Neo4jGraphRepository(self.driver)

        # Crear constraints automáticamente
        self.repo.ensure_constraints()

    # ---------- UPSERTS ----------

    def upsert_student(self, mongoId: str):
        return self.repo.upsert_student(mongoId)

    def upsert_institution(self, mongoId: str):
        return self.repo.upsert_institution(mongoId)

    def upsert_subject(self, name: str, institutionMongoId: str):
        return self.repo.upsert_subject(name, institutionMongoId)

    # ---------- RELATIONSHIPS ----------

    def link_studies_at(
        self,
        studentMongoId: str,
        institutionMongoId: str,
        startDate: str,
        endDate: str | None = None,
    ):
        return self.repo.link_studies_at(studentMongoId, institutionMongoId, startDate, endDate)

    def link_took(
        self,
        studentMongoId: str,
        subjectNeoId: str,
        year: int,
        grade: str,
    ):
        return self.repo.link_took(studentMongoId, subjectNeoId, year, grade)

    # def link_equivalent_to(
    #     self,
    #     fromSubjectId: str,
    #     toSubjectId: str,
    #     confidence: float = 1.0,
    #     source: str | None = None,
    # ):
    #     return self.repo.link_equivalent_to(fromSubjectId, toSubjectId, confidence, source)

    # ---------- READ QUERIES ----------

    def get_student_subjects(self, studentMongoId: str):
        return self.repo.get_student_subjects(studentMongoId)

    # def get_equivalents(self, subjectId: str, limit: int = 10):
    #     return self.repo.get_equivalents(subjectId, limit)

    # def recommend_subjects_for_student(self, studentId: str, limit: int = 10):
    #     return self.repo.recommend_subjects_for_student(studentId, limit)

# ---------- Función Factory ----------
_service = None

def get_neo4j_service():
    global _service
    if _service is None:
        _service = Neo4jGraphService()
    return _service