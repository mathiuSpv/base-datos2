from edugrade.core.neo4j_db import get_neo4j_driver
from edugrade.repository.neo4j_graph import Neo4jGraphRepository


class Neo4jGraphService:
    def __init__(self):
        self.driver = get_neo4j_driver()
        self.repo = Neo4jGraphRepository(self.driver)

        # Crear constraints automáticamente
        self.repo.ensure_constraints()

    # ---------- UPSERTS ----------

    def upsert_student(self, mongoId: str, fullName: str, country: str | None = None):
        return self.repo.upsert_student(mongoId, fullName, country)

    def upsert_institution(self, mongoId: str, name: str, country: str | None = None, level: str | None = None):
        return self.repo.upsert_institution(mongoId, name, country, level)

    def upsert_subject(self, mongoId: str, name: str, area: str | None = None, level: str | None = None):
        return self.repo.upsert_subject(mongoId, name, area, level)

    # ---------- RELATIONSHIPS ----------

    def link_studies_at(
        self,
        studentId: str,
        institutionId: str,
        startDate: str | None = None,
        endDate: str | None = None,
    ):
        return self.repo.link_studies_at(studentId, institutionId, startDate, endDate)

    def link_took(
        self,
        studentId: str,
        subjectId: str,
        grade1: float | None = None,
        grade2: float | None = None,
        general: float | None = None,
        startDate: str | None = None,
        endDate: str | None = None,
    ):
        return self.repo.link_took(studentId, subjectId, grade1, grade2, general, startDate, endDate)

    def link_equivalent_to(
        self,
        fromSubjectId: str,
        toSubjectId: str,
        confidence: float = 1.0,
        source: str | None = None,
    ):
        return self.repo.link_equivalent_to(fromSubjectId, toSubjectId, confidence, source)

    # ---------- READ QUERIES ----------

    def get_student_subjects(self, studentId: str):
        return self.repo.get_student_subjects(studentId)

    def get_equivalents(self, subjectId: str, limit: int = 10):
        return self.repo.get_equivalents(subjectId, limit)

    def recommend_subjects_for_student(self, studentId: str, limit: int = 10):
        return self.repo.recommend_subjects_for_student(studentId, limit)
