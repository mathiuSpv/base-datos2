from edugrade.services.neo4j_graph import get_neo4j_service

def main():
    neo = get_neo4j_service()

    # IDs fake de Mongo (solo strings, Neo no valida que sean ObjectId)
    student_id = "65f000000000000000000001"
    inst_id_1  = "65f000000000000000000101"  # UADE
    inst_id_2  = "65f000000000000000000102"  # UBA

    # 1) upsert student/institutions (solo mongoId)
    print("Upsert student:", neo.upsert_student(student_id))
    print("Upsert inst1:", neo.upsert_institution(inst_id_1))
    print("Upsert inst2:", neo.upsert_institution(inst_id_2))

    # 2) link studies_at (startDate obligatorio)
    print("Link studies_at UADE:", neo.link_studies_at(student_id, inst_id_1, "2022-03-01", "2024-12-01"))
    print("Link studies_at UBA:", neo.link_studies_at(student_id, inst_id_2, "2025-03-01", None))

    # 3) upsert subjects (ahora requieren institutionMongoId)
    sub1 = neo.upsert_subject("Programación 1", inst_id_2)              # UBA
    sub2 = neo.upsert_subject("Programación Algorítmica", inst_id_1)    # UADE
    sub3 = neo.upsert_subject("Algoritmos 1", inst_id_1)                # UADE

    print("Subjects:", sub1, sub2, sub3)

    # 4) link took (year/grade obligatorios)
    print("Link took sub1:", neo.link_took(student_id, sub1["id"], 2025, "UNI1"))
    print("Link took sub2:", neo.link_took(student_id, sub2["id"], 2025, "UNI1"))
    print("Link took sub3:", neo.link_took(student_id, sub3["id"], 2026, "UNI2"))

    # 5) read
    print("Student subjects:", neo.get_student_subjects(student_id))

if __name__ == "__main__":
    main()