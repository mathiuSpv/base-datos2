''' solo cypher + acceso a neo4j'''

from typing import Any, Dict, List, Optional
from neo4j import Driver

from app.models.neo4j import (
    LABEL_STUDENT,
    LABEL_INSTITUTION,
    LABEL_SUBJECT,
    REL_STUDIES_AT,
    REL_TOOK,
    REL_EQUIVALENT_TO,
)


class Neo4jRepo:
    def __init__(self, driver: Driver):
        self.driver = driver

    # ---------- UPSERT NODES ----------

    def upsert_student(self, mongoId: str, fullName: str, country: Optional[str] = None) -> Dict[str, Any]:
        cypher = f"""
        MERGE (s:{LABEL_STUDENT} {{mongoId: $mongoId}})
        SET s.fullName = $fullName,
            s.country  = $country
        RETURN s
        """
        params = {"mongoId": mongoId, "fullName": fullName, "country": country}
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            node = rec["s"]
            return dict(node)

    def upsert_institution(self, mongoId: str, name: str, country: Optional[str] = None, level: Optional[str] = None) -> Dict[str, Any]:
        cypher = f"""
        MERGE (i:{LABEL_INSTITUTION} {{mongoId: $mongoId}})
        SET i.name    = $name,
            i.country = $country,
            i.level   = $level
        RETURN i
        """
        params = {"mongoId": mongoId, "name": name, "country": country, "level": level}
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            node = rec["i"]
            return dict(node)

    def upsert_subject(self, mongoId: str, name: str, area: Optional[str] = None, level: Optional[str] = None) -> Dict[str, Any]:
        cypher = f"""
        MERGE (sub:{LABEL_SUBJECT} {{mongoId: $mongoId}})
        SET sub.name  = $name,
            sub.area  = $area,
            sub.level = $level
        RETURN sub
        """
        params = {"mongoId": mongoId, "name": name, "area": area, "level": level}
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            node = rec["sub"]
            return dict(node)

    # ---------- RELATIONSHIPS ----------

    def link_studies_at(
        self,
        studentId: str,
        institutionId: str,
        startDate: Optional[str] = None,
        endDate: Optional[str] = None,
    ) -> Dict[str, Any]:
        cypher = f"""
        MATCH (s:{LABEL_STUDENT} {{mongoId: $studentId}})
        MATCH (i:{LABEL_INSTITUTION} {{mongoId: $institutionId}})
        MERGE (s)-[r:{REL_STUDIES_AT}]->(i)
        SET r.startDate = $startDate,
            r.endDate   = $endDate
        RETURN r
        """
        params = {"studentId": studentId, "institutionId": institutionId, "startDate": startDate, "endDate": endDate}
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            rel = rec["r"]
            return dict(rel)

    def link_took(
        self,
        studentId: str,
        subjectId: str,
        grade1: Optional[float] = None,
        grade2: Optional[float] = None,
        general: Optional[float] = None,
        startDate: Optional[str] = None,
        endDate: Optional[str] = None,
    ) -> Dict[str, Any]:
        cypher = f"""
        MATCH (s:{LABEL_STUDENT} {{mongoId: $studentId}})
        MATCH (sub:{LABEL_SUBJECT} {{mongoId: $subjectId}})
        MERGE (s)-[r:{REL_TOOK}]->(sub)
        SET r.grade1    = $grade1,
            r.grade2    = $grade2,
            r.general   = $general,
            r.startDate = $startDate,
            r.endDate   = $endDate
        RETURN r
        """
        params = {
            "studentId": studentId,
            "subjectId": subjectId,
            "grade1": grade1,
            "grade2": grade2,
            "general": general,
            "startDate": startDate,
            "endDate": endDate,
        }
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            rel = rec["r"]
            return dict(rel)

    def link_equivalent_to(
        self,
        fromSubjectId: str,
        toSubjectId: str,
        confidence: float = 1.0,
        source: Optional[str] = None,
    ) -> Dict[str, Any]:
        cypher = f"""
        MATCH (a:{LABEL_SUBJECT} {{mongoId: $fromSubjectId}})
        MATCH (b:{LABEL_SUBJECT} {{mongoId: $toSubjectId}})
        MERGE (a)-[r:{REL_EQUIVALENT_TO}]->(b)
        SET r.confidence = $confidence,
            r.source     = $source
        RETURN r
        """
        params = {"fromSubjectId": fromSubjectId, "toSubjectId": toSubjectId, "confidence": confidence, "source": source}
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            rel = rec["r"]
            return dict(rel)

    # ---------- QUERIES (READ) ----------

    def get_student_subjects(self, studentId: str) -> List[Dict[str, Any]]:
        cypher = f"""
        MATCH (s:{LABEL_STUDENT} {{mongoId: $studentId}})-[r:{REL_TOOK}]->(sub:{LABEL_SUBJECT})
        RETURN sub, r
        ORDER BY coalesce(r.endDate, "") DESC
        """
        with self.driver.session() as session:
            results = session.run(cypher, {"studentId": studentId})
            out: List[Dict[str, Any]] = []
            for rec in results:
                sub = dict(rec["sub"])
                rel = dict(rec["r"])
                out.append({"subject": sub, "took": rel})
            return out

    def get_equivalents(self, subjectId: str, limit: int = 10) -> List[Dict[str, Any]]:
        cypher = f"""
        MATCH (sub:{LABEL_SUBJECT} {{mongoId: $subjectId}})-[r:{REL_EQUIVALENT_TO}]->(eq:{LABEL_SUBJECT})
        RETURN eq, r
        ORDER BY coalesce(r.confidence, 0) DESC
        LIMIT $limit
        """
        with self.driver.session() as session:
            results = session.run(cypher, {"subjectId": subjectId, "limit": limit})
            out: List[Dict[str, Any]] = []
            for rec in results:
                eq = dict(rec["eq"])
                rel = dict(rec["r"])
                out.append({"equivalent": eq, "relation": rel})
            return out

    def recommend_subjects_for_student(self, studentId: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recomendación simple:
        - mismos institutos que el estudiante
        - materias tomadas por otros estudiantes de esas instituciones
        - que el estudiante aún no tomó
        """
        cypher = f"""
        MATCH (me:{LABEL_STUDENT} {{mongoId: $studentId}})-[:{REL_STUDIES_AT}]->(inst:{LABEL_INSTITUTION})<-[:{REL_STUDIES_AT}]-(other:{LABEL_STUDENT})-[:{REL_TOOK}]->(sub:{LABEL_SUBJECT})
        WHERE NOT (me)-[:{REL_TOOK}]->(sub)
        RETURN sub, count(*) AS score
        ORDER BY score DESC
        LIMIT $limit
        """
        with self.driver.session() as session:
            results = session.run(cypher, {"studentId": studentId, "limit": limit})
            out: List[Dict[str, Any]] = []
            for rec in results:
                sub = dict(rec["sub"])
                out.append({"subject": sub, "score": rec["score"]})
            return out
