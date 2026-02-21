from edugrade.services.neo4j_graph import get_neo4j_service

def main():
    neo = get_neo4j_service()

    # IDs fake de Mongo (solo strings, Neo no valida que sean ObjectId)
    student_id = "65f000000000000000000001"
    inst_id_1  = "65f000000000000000000101"
    inst_id_2  = "65f000000000000000000102"

    # 1) upsert student/institutions (solo mongoId)
    print("Upsert student:", neo.upsert_student(student_id))
    print("Upsert inst1:", neo.upsert_institution(inst_id_1))
    print("Upsert inst2:", neo.upsert_institution(inst_id_2))

    # 2) link studies_at (startDate obligatorio)
    print("Link studies_at UADE:", neo.link_studies_at(student_id, inst_id_1, "2022-03-01", "2024-12-01"))
    print("Link studies_at UBA:", neo.link_studies_at(student_id, inst_id_2, "2025-03-01", None))

    # 3) upsert subjects (Neo) y link took (year/grade obligatorios)
    sub1 = neo.upsert_subject("Programación 1")
    sub2 = neo.upsert_subject("Programación Algorítmica")
    sub3 = neo.upsert_subject("Algoritmos 1")

    print("Subjects:", sub1, sub2, sub3)

    print("Link took sub1:", neo.link_took(student_id, sub1["id"], 2025, "UNI1"))
    print("Link took sub2:", neo.link_took(student_id, sub2["id"], 2025, "UNI1"))
    print("Link took sub3:", neo.link_took(student_id, sub3["id"], 2026, "UNI2"))

    # 4) read
    print("Student subjects:", neo.get_student_subjects(student_id))

if __name__ == "__main__":
    main()