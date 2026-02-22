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
    
    def delete_student(self, mongoId: str):
        return self.repo.delete_student(mongoId)

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
        subjectId: str,
        startDate: str,
        grade: str,
        endDate: str | None = None,
    ):
        return self.repo.link_took(studentMongoId, subjectId, startDate, grade, endDate)

    def add_equivalence(self, fromSubjectId: str, toSubjectId: str, levelStage: str):
        return self.repo.add_equivalence(fromSubjectId, toSubjectId, levelStage)
    
    def unlink_equivalence_by_subject(self, subjectId: str, levelStage: str):
        return self.repo.unlink_equivalence_by_subject(subjectId, levelStage)    
    
    def are_equivalent_by_cycle(self, aId: str, bId: str, levelStage: str):
        return self.repo.are_equivalent_by_cycle(aId, bId, levelStage)

    # ---------- READ QUERIES ----------

    def get_student_subjects(self, studentMongoId: str):
        return self.repo.get_student_subjects(studentMongoId)
    
    def get_equivalences_group(self, subjectId: str, levelStage: str):
        return self.repo.get_equivalences_group(subjectId, levelStage)
    
    def get_student_institutions(self, studentId: str):
        return self.repo.get_institutions_by_student(studentId)
    
    def get_student_subject_took(self, studentMongoId: str, subjectId: str):
        return self.repo.get_student_subject_took(studentMongoId, subjectId)
    
    def get_subjects_by_institution(self, institutionMongoId: str):
        return self.repo.get_subjects_by_institution(institutionMongoId)

    # def recommend_subjects_for_student(self, studentId: str, limit: int = 10):
    #     return self.repo.recommend_subjects_for_student(studentId, limit)

# ---------- Función Factory ----------
_service = None

def get_neo4j_service():
    global _service
    if _service is None:
        _service = Neo4jGraphService()
    return _service