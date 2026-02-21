''' solo cypher + acceso a neo4j'''

from typing import Any, Dict, List, Optional
from neo4j import Driver

from edugrade.models.neo4j import (
    LABEL_STUDENT,
    LABEL_INSTITUTION,
    LABEL_SUBJECT,
    REL_STUDIES_AT,
    REL_TOOK,
#    REL_EQUIVALENT_TO, por ahora no porque no usamos equivalent -> schemas/neo4j_relations.py
)


class Neo4jGraphRepository:
    def __init__(self, driver: Driver):
        self.driver = driver

    def ensure_constraints(self) -> None:
        with self.driver.session() as session:
            session.run("""
                CREATE CONSTRAINT student_mongoId IF NOT EXISTS
                FOR (s:Student) REQUIRE s.mongoId IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT institution_mongoId IF NOT EXISTS
                FOR (i:Institution) REQUIRE i.mongoId IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT subject_name IF NOT EXISTS
                FOR (sub:Subject) REQUIRE sub.name IS UNIQUE
            """)
            
    # ---------- UPSERT NODES ----------

    def upsert_student(self, mongoId: str, fullName: str, nationality: Optional[str] = None) -> Dict[str, Any]:
        cypher = f"""
        MERGE (s:{LABEL_STUDENT} {{mongoId: $mongoId}})
        SET s.fullName = $fullName,
            s.nationality = $nationality
        RETURN s
        """
        params = {"mongoId": mongoId, "fullName": fullName, "nationality": nationality}
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            return dict(rec["s"])

    def upsert_institution(
        self,
        mongoId: str,
        name: str,
        country: Optional[str] = None,
    ) -> Dict[str, Any]:
        cypher = f"""
        MERGE (i:{LABEL_INSTITUTION} {{mongoId: $mongoId}})
        SET i.name    = $name,
            i.country = $country
        RETURN i
        """
        params = {
            "mongoId": mongoId,
            "name": name,
            "country": country,
        }
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            return dict(rec["i"])

    def upsert_subject(self, name: str) -> Dict[str, Any]:
        cypher = f"""
        MERGE (sub:{LABEL_SUBJECT} {{name: $name}})
        RETURN id(sub) AS id, sub.name AS name
        """
        with self.driver.session() as session:
            rec = session.run(cypher, {"name": name}).single()
            if rec is None:
                raise ValueError("Failed to upsert subject")
            return {
                "id": str(rec["id"]),
                "name": rec["name"],
            }

    # ---------- RELATIONSHIPS ----------

    def link_studies_at(
        self,
        studentMongoId: str,
        institutionMongoId: str,
        startDate: Optional[str] = None,
        endDate: Optional[str] = None,
    ) -> Dict[str, Any]:
        cypher = f"""
        MATCH (s:{LABEL_STUDENT} {{mongoId: $studentMongoId}})
        MATCH (i:{LABEL_INSTITUTION} {{mongoId: $institutionMongoId}})
        MERGE (s)-[r:{REL_STUDIES_AT}]->(i)
        SET r.startDate = $startDate,
            r.endDate   = $endDate
        RETURN r
        """
        params = {"studentMongoId": studentMongoId, "institutionMongoId": institutionMongoId, "startDate": startDate, "endDate": endDate}
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            if rec is None:
                raise ValueError(f"Not found: studentMongoId={studentMongoId} or institutionMongoId={institutionMongoId}")
            # Si studentMongoId o institutionId no existe, match no encuentra nada: single(), sin esto devuelve None
            # mismo procedimiento en link_* took y equivalent_to
            return dict(rec["r"])

    def link_took(
        self,
        studentMongoId: str,
        subjectNeoId: str,
        year: Optional[int] = None,
        grade: Optional[str] = None,
    ) -> Dict[str, Any]:
        cypher = f"""
        MATCH (s:{LABEL_STUDENT} {{mongoId: $studentMongoId}})
        MATCH (sub:{LABEL_SUBJECT})
        WHERE id(sub) = $subjectNeoId
        MERGE (s)-[r:{REL_TOOK}]->(sub)
        SET r.year  = $year,
            r.grade = $grade
        RETURN r
        """
        params = {
            "studentMongoId": studentMongoId,
            "subjectNeoId": int(subjectNeoId),  # Neo internal id es int
            "year": year,
            "grade": grade,
        }
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            if rec is None:
                raise ValueError(f"Not found: studentMongoId={studentMongoId} or subjectNeoId={subjectNeoId}")
            return dict(rec["r"])

    # def link_equivalent_to(
    #     self,
    #     fromSubjectId: str,
    #     toSubjectId: str,
    #     confidence: float = 1.0,
    #     source: Optional[str] = None,
    # ) -> Dict[str, Any]:
    #     cypher = f"""
    #     MATCH (a:{LABEL_SUBJECT} {{mongoId: $fromSubjectId}})
    #     MATCH (b:{LABEL_SUBJECT} {{mongoId: $toSubjectId}})
    #     MERGE (a)-[r:{REL_EQUIVALENT_TO}]->(b)
    #     SET r.confidence = $confidence,
    #         r.source     = $source
    #     RETURN r
    #     """
    #     params = {"fromSubjectId": fromSubjectId, "toSubjectId": toSubjectId, "confidence": confidence, "source": source}
    #     with self.driver.session() as session:
    #         rec = session.run(cypher, params).single()
    #         if rec is None:
    #             raise ValueError(f"Not found: Subject(s) -> fromSubjectId={fromSubjectId} or toSubjectId={toSubjectId} not found")
    #         return dict(rec["r"])

    # ---------- QUERIES (READ) ----------

    def get_student_subjects(self, studentMongoId: str) -> List[Dict[str, Any]]:
        cypher = f"""
        MATCH (s:{LABEL_STUDENT} {{mongoId: $studentMongoId}})-[r:{REL_TOOK}]->(sub:{LABEL_SUBJECT})
        RETURN id(sub) AS subjectId, sub, r
        ORDER BY coalesce(r.year, 0) DESC
        """
        with self.driver.session() as session:
            results = session.run(cypher, {"studentMongoId": studentMongoId})
            out: List[Dict[str, Any]] = []
            for rec in results:
                out.append({
                    "subject": {"id": str(rec["subjectId"]), **dict(rec["sub"])},
                    "took": dict(rec["r"])
                })
            return out

    # def get_equivalents(self, subjectId: str, limit: int = 10) -> List[Dict[str, Any]]:
    #     cypher = f"""
    #     MATCH (sub:{LABEL_SUBJECT} {{mongoId: $subjectId}})-[r:{REL_EQUIVALENT_TO}]->(eq:{LABEL_SUBJECT})
    #     RETURN eq, r
    #     ORDER BY coalesce(r.confidence, 0) DESC
    #     LIMIT $limit
    #     """
    #     with self.driver.session() as session:
    #         results = session.run(cypher, {"subjectId": subjectId, "limit": limit})
    #         out: List[Dict[str, Any]] = []
    #         for rec in results:
    #             out.append({"equivalent": dict(rec["eq"]), "relation": dict(rec["r"])})
    #         return out

    # def recommend_subjects_for_student(self, studentId: str, limit: int = 10) -> List[Dict[str, Any]]:
    #     cypher = f"""
    #     MATCH (me:{LABEL_STUDENT} {{mongoId: $studentId}})-[:{REL_STUDIES_AT}]->(inst:{LABEL_INSTITUTION})<-[:{REL_STUDIES_AT}]-(other:{LABEL_STUDENT})-[:{REL_TOOK}]->(sub:{LABEL_SUBJECT})
    #     WHERE NOT (me)-[:{REL_TOOK}]->(sub)
    #     RETURN sub, count(*) AS score
    #     ORDER BY score DESC
    #     LIMIT $limit
    #     """
    #     with self.driver.session() as session:
    #         results = session.run(cypher, {"studentId": studentId, "limit": limit})
    #         out: List[Dict[str, Any]] = []
    #         for rec in results:
    #             out.append({"subject": dict(rec["sub"]), "score": rec["score"]})
    #         return out
