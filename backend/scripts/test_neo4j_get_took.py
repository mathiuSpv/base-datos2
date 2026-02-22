from edugrade.services.neo4j_graph import get_neo4j_service

def main():
    neo = get_neo4j_service()

    student_id = "65f000000000000000000001"
    inst_id_1  = "65f000000000000000000101"  # UADE

    print("Upsert student:", neo.upsert_student(student_id))
    print("Upsert inst:", neo.upsert_institution(inst_id_1))

    # Crear 2 materias
    sub1 = neo.upsert_subject("Bases de Datos 2", inst_id_1)
    sub2 = neo.upsert_subject("Estructuras de Datos", inst_id_1)
    print("Subjects:", sub1, sub2)

    # Link TOOK con start/end (sub1 finalizada, sub2 en curso)
    print("Link took sub1:", neo.link_took(student_id, sub1["id"], "2025-03-01", "UNI2", "2025-12-01"))
    print("Link took sub2:", neo.link_took(student_id, sub2["id"], "2026-03-01", "UNI3", None))

    # ✅ Test principal: traer relación puntual student + subject
    print("\n--- GET TOOK (student + sub1) ---")
    res1 = neo.get_student_subject_took(student_id, sub1["id"])
    print(res1)

    print("\n--- GET TOOK (student + sub2) ---")
    res2 = neo.get_student_subject_took(student_id, sub2["id"])
    print(res2)

    # ❌ Caso negativo: subjectId que no existe
    print("\n--- GET TOOK (subject inexistente) ---")
    res3 = neo.get_student_subject_took(student_id, "00000000-0000-0000-0000-000000000000")
    print(res3)

    # ❌ Caso negativo: studentId que no existe
    print("\n--- GET TOOK (student inexistente) ---")
    res4 = neo.get_student_subject_took("65f999999999999999999999", sub1["id"])
    print(res4)

if __name__ == "__main__":
    main()