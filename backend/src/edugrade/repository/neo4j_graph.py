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
        
    def delete_student(self, mongoId: str) -> Dict[str, Any]:
        cypher = f"""
        MATCH (s:{LABEL_STUDENT} {{mongoId: $mongoId}})
        WITH s, s.mongoId AS id
        DETACH DELETE s
        RETURN id AS mongoId
        """
        with self.driver.session() as session:
            rec = session.run(cypher, {"mongoId": mongoId}).single()
            if rec is None:
                return {"deleted": False, "mongoId": mongoId}
            return {"deleted": True, "mongoId": rec["mongoId"]}

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
        subjectId: str,          # UUID
        startDate: str,          # ISO string
        grade: str,
        endDate: Optional[str] = None,
    ) -> Dict[str, Any]:
        cypher = f"""
        MATCH (s:{LABEL_STUDENT} {{mongoId: $studentMongoId}})
        MATCH (sub:{LABEL_SUBJECT} {{id: $subjectId}})
        MERGE (s)-[r:{REL_TOOK}]->(sub)
        SET r.startDate = $startDate,
            r.endDate   = $endDate,
            r.grade     = $grade
        RETURN r
        """
        params = {
            "studentMongoId": studentMongoId,
            "subjectId": subjectId,
            "startDate": startDate,
            "endDate": endDate,
            "grade": grade,
        }
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            if rec is None:
                raise ValueError(f"Not found: studentMongoId={studentMongoId} or subjectId={subjectId}")
            return dict(rec["r"])

    def add_equivalence(self, fromId: str, toId: str, levelStage: str) -> Dict[str, Any]:
        if fromId == toId:
            raise ValueError("fromSubjectId and toSubjectId must be different")

        cypher = f"""
        MATCH (a:{LABEL_SUBJECT} {{id:$fromId}})
        MATCH (b:{LABEL_SUBJECT} {{id:$toId}})

        // si ya hay arista directa, listo
        OPTIONAL MATCH (a)-[existing:{REL_EQUIVALENT_TO} {{levelStage:$levelStage}}]->(b)

        // detectar si a está en un grupo (tiene succ y pred)
        OPTIONAL MATCH (a)-[a_out:{REL_EQUIVALENT_TO} {{levelStage:$levelStage}}]->(a_succ:{LABEL_SUBJECT})
        OPTIONAL MATCH (a_pred:{LABEL_SUBJECT})-[a_in:{REL_EQUIVALENT_TO} {{levelStage:$levelStage}}]->(a)

        // detectar si b ya está en algún grupo
        OPTIONAL MATCH (b)-[:{REL_EQUIVALENT_TO} {{levelStage:$levelStage}}]->(:{LABEL_SUBJECT})
        OPTIONAL MATCH (:{LABEL_SUBJECT})-[:{REL_EQUIVALENT_TO} {{levelStage:$levelStage}}]->(b)

        WITH a,b,existing,a_succ,a_out,a_pred,a_in,
            CASE
            WHEN existing IS NOT NULL THEN 'ALREADY_DIRECT'
            WHEN a_succ IS NULL AND a_pred IS NULL THEN 'A_ISOLATED'
            ELSE 'A_IN_GROUP'
            END AS a_state,
            CASE
            WHEN ( (b)-[:{REL_EQUIVALENT_TO} {{levelStage:$levelStage}}]->() ) OR ( ()-[:{REL_EQUIVALENT_TO} {{levelStage:$levelStage}}]->(b) )
            THEN true ELSE false
            END AS b_in_group

        // si b ya está en un grupo, por ahora no mezclamos grupos
        WITH a,b,existing,a_succ,a_out,a_state,b_in_group
        WHERE NOT b_in_group

        // CASO 1: A y B aislados => par bidireccional
        FOREACH (_ IN CASE WHEN a_state='A_ISOLATED' THEN [1] ELSE [] END |
        MERGE (a)-[r1:{REL_EQUIVALENT_TO} {{levelStage:$levelStage}}]->(b)
        ON CREATE SET r1.createdAt = datetime()
        MERGE (b)-[r2:{REL_EQUIVALENT_TO} {{levelStage:$levelStage}}]->(a)
        ON CREATE SET r2.createdAt = datetime()
        )

        // CASO 2: A está en grupo (ciclo) y B aislado => insertar B "después" de A
        // a -> a_succ pasa a ser: a -> b -> a_succ
        FOREACH (_ IN CASE WHEN a_state='A_IN_GROUP' THEN [1] ELSE [] END |
        DELETE a_out
        MERGE (a)-[r3:{REL_EQUIVALENT_TO} {{levelStage:$levelStage}}]->(b)
        ON CREATE SET r3.createdAt = datetime()
        MERGE (b)-[r4:{REL_EQUIVALENT_TO} {{levelStage:$levelStage}}]->(a_succ)
        ON CREATE SET r4.createdAt = datetime()
        )

        RETURN true AS ok, a_state AS aState, b_in_group AS bWasInGroup;
        """

        params = {"fromId": fromId, "toId": toId, "levelStage": str(levelStage)}
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            if rec is None:
                # o b estaba en grupo (bloqueado) o no encontró nodos
                raise ValueError("Cannot add equivalence: subject not found or target is already in another group")
            return {"ok": True, "aState": rec["aState"], "bWasInGroup": rec["bWasInGroup"]}

    def unlink_equivalence_by_subject(self, subjectId: str, levelStage: str) -> Dict[str, Any]:
        cypher = f"""
        MATCH (s:{LABEL_SUBJECT} {{id: $subjectId}})

        OPTIONAL MATCH (pred:{LABEL_SUBJECT})-[rin:{REL_EQUIVALENT_TO} {{levelStage: $levelStage}}]->(s)
        OPTIONAL MATCH (s)-[rout:{REL_EQUIVALENT_TO} {{levelStage: $levelStage}}]->(succ:{LABEL_SUBJECT})

        WITH s, pred, succ, rin, rout
        WHERE pred IS NOT NULL AND succ IS NOT NULL

        WITH s, pred, succ, rin, rout,
            CASE WHEN pred.id = succ.id THEN 'PAIR' ELSE 'CYCLE' END AS kind

        // borrar aristas que conectan a s dentro del grupo
        DELETE rin
        DELETE rout

        // si era ciclo (>=3), puenteo pred -> succ para mantener ciclo
        FOREACH (_ IN CASE WHEN kind = 'CYCLE' THEN [1] ELSE [] END |
            MERGE (pred)-[rnew:{REL_EQUIVALENT_TO} {{levelStage: $levelStage}}]->(succ)
            ON CREATE SET rnew.createdAt = datetime()
        )

        RETURN true AS deleted, kind AS kind, pred.id AS predecessorId, succ.id AS successorId, s.id AS removedId
        """

        params = {"subjectId": subjectId, "levelStage": str(levelStage)}
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()

            if rec is None:
                # no tenía pred o succ en ese levelStage -> no pertenece a grupo
                return {"deleted": False}

            return {
                "deleted": bool(rec["deleted"]),
                "kind": rec["kind"],              # 'PAIR' o 'CYCLE'
                "removedId": rec["removedId"],
                "predecessorId": rec["predecessorId"],
                "successorId": rec["successorId"],
            }
    
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


    # ---------- QUERIES (READ) ----------

    def get_student_subjects(self, studentMongoId: str) -> List[Dict[str, Any]]:
        cypher = f"""
        MATCH (s:{LABEL_STUDENT} {{mongoId: $studentMongoId}})-[r:{REL_TOOK}]->(sub:{LABEL_SUBJECT})
        RETURN sub.id AS subjectId, sub, r
        ORDER BY coalesce(r.startDate, "") DESC
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

    # ESTE TE PIDE LA LEVELSTAGE PARA DARTE TODAS LAS MATERIAS EQUIVALENTES DEL GRUPO QUE PERTENECE A UNA MATERIA    
    def get_equivalences_group(self, subjectId: str, levelStage: str) -> List[Dict[str, Any]]:
        cypher = f"""
        MATCH (s:{LABEL_SUBJECT} {{id: $subjectId}})
        MATCH p = (s)-[:{REL_EQUIVALENT_TO}*0..]-(eq:{LABEL_SUBJECT})
        WHERE ALL(r IN relationships(p) WHERE toString(r.levelStage) = toString($levelStage))
        RETURN DISTINCT
            eq.id AS id,
            eq.name AS name,
            eq.institutionMongoId AS institutionMongoId
        ORDER BY coalesce(name, "") ASC
        """
        params = {"subjectId": subjectId, "levelStage": levelStage}
        with self.driver.session() as session:
            res = session.run(cypher, params)
            return [dict(r) for r in res]


    def get_institutions_by_student(self, studentId: str):
        query = """
        MATCH (s:Student {mongoId: $studentId})-[:STUDIES_AT]->(i:Institution)
        RETURN i.mongoId AS mongoId,
            i.name AS name,
            i.country AS country,
            i.level AS level
        """

        with self.driver.session() as session:
            result = session.run(query, studentId=studentId)
            return [record.data() for record in result]

    def get_student_subject_took(self, studentMongoId: str, subjectId: str) -> Dict[str, Any]: # datos de la relacion estudiante materia
        cypher = f"""
        MATCH (s:{LABEL_STUDENT} {{mongoId: $studentMongoId}})-[r:{REL_TOOK}]->(sub:{LABEL_SUBJECT} {{id: $subjectId}})
        RETURN s, sub, r
        """
        params = {"studentMongoId": studentMongoId, "subjectId": subjectId}
        with self.driver.session() as session:
            rec = session.run(cypher, params).single()
            if rec is None:
                return {"found": False}
            return {
                "found": True,
                "student": dict(rec["s"]),
                "subject": {"id": str(rec["sub"]["id"]), **dict(rec["sub"])},
                "took": dict(rec["r"]),  # startDate, endDate, grade
            }
        
    def get_subjects_by_institution(self, institutionMongoId: str) -> List[Dict[str, Any]]:
        cypher = f"""
        MATCH (sub:{LABEL_SUBJECT} {{institutionMongoId: $institutionMongoId}})
        RETURN sub.id AS id, sub.name AS name, sub.institutionMongoId AS institutionMongoId
        ORDER BY toLower(sub.name) ASC
        """
        with self.driver.session() as session:
            res = session.run(cypher, {"institutionMongoId": institutionMongoId})
            return [dict(r) for r in res]

