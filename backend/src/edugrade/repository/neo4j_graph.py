''' solo cypher + acceso a neo4j'''

from typing import Any, Dict, List, Optional
from neo4j import Driver

from edugrade.models.neo4j import (
    LABEL_STUDENT,
    LABEL_INSTITUTION,
    LABEL_SUBJECT,
    REL_STUDIES_AT,
    REL_TOOK,
    REL_EQUIVALENT_TO,
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
                CREATE CONSTRAINT subject_id IF NOT EXISTS
                FOR (sub:Subject) REQUIRE sub.id IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT subject_unique IF NOT EXISTS
                FOR (sub:Subject) REQUIRE (sub.name, sub.institutionMongoId) IS UNIQUE
            """)
            
    # ---------- UPSERT NODES ----------

    def upsert_student(self, mongoId: str) -> Dict[str, Any]:
        cypher = f"""
        MERGE (s:{LABEL_STUDENT} {{mongoId: $mongoId}})
        RETURN s
        """
        with self.driver.session() as session:
            rec = session.run(cypher, {"mongoId": mongoId}).single()
            return dict(rec["s"])

    def upsert_institution(self, mongoId: str) -> Dict[str, Any]:
        cypher = f"""
        MERGE (i:{LABEL_INSTITUTION} {{mongoId: $mongoId}})
        RETURN i
        """
        with self.driver.session() as session:
            rec = session.run(cypher, {"mongoId": mongoId}).single()
            return dict(rec["i"])

    def upsert_subject(self, name: str, institutionMongoId: str) -> Dict[str, Any]:
        cypher = f"""
        MERGE (sub:{LABEL_SUBJECT} {{name: $name, institutionMongoId: $institutionMongoId}})
        ON CREATE SET sub.id = randomUUID()
        RETURN sub.id AS id, sub.name AS name, sub.institutionMongoId AS institutionMongoId
        """
        params = {"name": name, "institutionMongoId": institutionMongoId}
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            if rec is None:
                raise ValueError("Failed to upsert subject")
            return {
                "id": str(rec["id"]),
                "name": rec["name"],
                "institutionMongoId": rec["institutionMongoId"],
            }

    # ---------- RELATIONSHIPS ----------

    def link_studies_at(
        self,
        studentMongoId: str,
        institutionMongoId: str,
        startDate: str,
        endDate: Optional[str] = None,
    ) -> Dict[str, Any]:
        cypher = f"""
        MATCH (s:{LABEL_STUDENT} {{mongoId: $studentMongoId}})
        MATCH (i:{LABEL_INSTITUTION} {{mongoId: $institutionMongoId}})
        MERGE (s)-[r:{REL_STUDIES_AT} {{startDate: $startDate}}]->(i)
        SET r.endDate = $endDate
        RETURN r
        """
        params = {
            "studentMongoId": studentMongoId,
            "institutionMongoId": institutionMongoId,
            "startDate": startDate,
            "endDate": endDate,
        }
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            if rec is None:
                raise ValueError(
                    f"Not found: studentMongoId={studentMongoId} or institutionMongoId={institutionMongoId}"
                )
            return dict(rec["r"])

    def link_took(
        self,
        studentMongoId: str,
        subjectId: str,   # ahora es UUID
        year: int,
        grade: str,
    ) -> Dict[str, Any]:
        cypher = f"""
        MATCH (s:{LABEL_STUDENT} {{mongoId: $studentMongoId}})
        MATCH (sub:{LABEL_SUBJECT} {{id: $subjectId}})
        MERGE (s)-[r:{REL_TOOK}]->(sub)
        SET r.year  = $year,
            r.grade = $grade
        RETURN r
        """
        params = {
            "studentMongoId": studentMongoId,
            "subjectId": subjectId,  # UUID string
            "year": year,
            "grade": grade,
        }
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            if rec is None:
                raise ValueError(f"Not found: studentMongoId={studentMongoId} or subjectId={subjectId}")
            return dict(rec["r"])

    def link_equivalent_to(self, fromSubjectId: str, toSubjectId: str, levelStage: str) -> Dict[str, Any]:
        if fromSubjectId == toSubjectId:
            raise ValueError("fromSubjectId and toSubjectId must be different")

        cypher = f"""
        MATCH (a:{LABEL_SUBJECT} {{id: $fromSubjectId}})
        MATCH (b:{LABEL_SUBJECT} {{id: $toSubjectId}})
        MERGE (a)-[r:{REL_EQUIVALENT_TO} {{levelStage: $levelStage}}]->(b)
        ON CREATE SET r.createdAt = datetime()
        RETURN r
        """
        params = {"fromSubjectId": fromSubjectId, "toSubjectId": toSubjectId, "levelStage": levelStage}
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            if rec is None:
                raise ValueError(f"Not found: fromSubjectId={fromSubjectId} or toSubjectId={toSubjectId}")
            return dict(rec["r"])

    # ---------- QUERIES (READ) ----------

    def get_student_subjects(self, studentMongoId: str) -> List[Dict[str, Any]]:
        cypher = f"""
        MATCH (s:{LABEL_STUDENT} {{mongoId: $studentMongoId}})-[r:{REL_TOOK}]->(sub:{LABEL_SUBJECT})
        RETURN sub.id AS subjectId, sub, r
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

    def are_equivalent_by_cycle(self, aId: str, bId: str, levelStage: str) -> bool:
        cypher = f"""
        MATCH (a:{LABEL_SUBJECT} {{id: $aId}})
        MATCH (b:{LABEL_SUBJECT} {{id: $bId}})

        OPTIONAL MATCH p1 = (a)-[:{REL_EQUIVALENT_TO}*1..]->(b)
        OPTIONAL MATCH p2 = (b)-[:{REL_EQUIVALENT_TO}*1..]->(a)

        WITH p1, p2
        WHERE p1 IS NOT NULL
        AND p2 IS NOT NULL
        AND ALL(r IN relationships(p1) WHERE toString(r.levelStage) = $levelStage)
        AND ALL(r IN relationships(p2) WHERE toString(r.levelStage) = $levelStage)

        RETURN true AS equivalent
        """
        params = {"aId": aId, "bId": bId, "levelStage": levelStage}
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            return bool(rec) and bool(rec["equivalent"])

