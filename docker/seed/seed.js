/* eslint-disable no-undef */
print("🌱 Seeding MongoDB (minimal, aligned with Neo4j)...");
const dbx = db.getSiblingDB("edugrade");
dbx.dropDatabase();
print("✅ Dropped database edugrade");

// Fixed IDs (must match Neo4j mongoId properties)
const studentMatiasId = ObjectId("76c23cb6d9834dc12a9e2f14");
const studentHomerId = ObjectId("5f1d7f3e8b9c4a1a2b3c4d5e");
const inst_chl_secondary = ObjectId("c549bc38c0614170f01a2fef");
const inst_arg_secondary = ObjectId("d2f1e3a4b5c67890abcdef12");
const inst_uba = ObjectId("501b6ff69b36d251d142e796");
const inst_uade = ObjectId("6aa06d4942ac05800eb4b57f");
const inst_uk_inst = ObjectId("07cc736e090e75966d562a9b");
const inst_us_inst = ObjectId("1cd767efc7bae3e6bd19574d");
const inst_de_inst = ObjectId("9802a6b16aba871af182b6cb");

// Students
dbx.students.insertOne({ _id: studentMatiasId, identity: "94758658", firstName: "Matias Ignacio", lastName: "Pomareda Vasquez", birthDate: new Date("2000-05-17T00:00:00.000Z"), nationality: "ARG" });
dbx.students.insertOne({ _id: studentHomerId, identity: "440865034", firstName: "Homero", lastName: "Gonzales", birthDate: new Date("2000-05-17T00:00:00.000Z"), nationality: "ARG" });
print("✅ Inserted students:", dbx.students.countDocuments());

dbx.institutions.insertMany([
  { _id: inst_chl_secondary, name: "Liceo Secundario Ejemplo (Chile)", country: "CHL", address: "Santiago, Chile" },
  { _id: inst_arg_secondary, name: "Instituto Dr. Jose Ingenieros", country: "ARG", address: "CABA, Argentina" },
  { _id: inst_uba, name: "Universidad de Buenos Aires", country: "ARG", address: "CABA, Argentina" },
  { _id: inst_uade, name: "Universidad Argentina de la Empresa", country: "ARG", address: "CABA, Argentina" },
  { _id: inst_uk_inst, name: "University of Oxford", country: "UK", address: "Oxford, United Kingdom" },
  { _id: inst_us_inst, name: "Massachusetts Institute of Technology", country: "US", address: "Cambridge, MA, USA" },
  { _id: inst_de_inst, name: "Technische Universität München", country: "DE", address: "Munich, Germany" },
]);
print("✅ Inserted institutions:", dbx.institutions.countDocuments());

dbx.options.updateOne(
  { key: "grade" },
  {
    $set: {
      key: "grade",
      response: {
        "1": "Grade 1 (Primary School)",
        "2": "Grade 2 (Primary School)",
        "3": "Grade 3 (Primary School)",
        "4": "Grade 4 (Primary School)",
        "5": "Grade 5 (Primary School)",
        "6": "Grade 6 (Primary School)",
        "7": "Grade 7 (Primary School)",
        "8": "Grade 8 (Secondary School)",
        "9": "Grade 9 (Secondary School)",
        "10": "Grade 10 (Secondary School)",
        "11": "Grade 11 (Secondary School)",
        "12": "Grade 12 (Matric - National Senior Certificate)",
        "13": "N1 (TVET College)",
        "14": "N2 (TVET College)",
        "15": "N3 (TVET College)",
        "16": "N4 (TVET College)",
        "17": "N5 (TVET College)",
        "18": "N6 (TVET College)",
        "19": "1st Year Undergraduate",
        "20": "2nd Year Undergraduate",
        "21": "3rd Year Undergraduate",
        "22": "4th Year Undergraduate",
        "23": "Honours Degree",
        "24": "Master’s Degree",
        "25": "Doctoral Degree (PhD)"
      }
    }
  },
  { upsert: true }
);
print("✅ Upserted options: grade");

dbx.conversionRules.updateOne({ system: "AR_1_10", country: "ARG", grade: "19", validFrom: ISODate("2020-01-01T00:00:00.000Z") }, { $set: { system: "AR_1_10", country: "ARG", grade: "19", validFrom: ISODate("2020-01-01T00:00:00.000Z"), validTo: null, map: { "1": "1", "2": "1.5", "3": "2", "4": "2.5", "5": "3", "6": "4", "7": "5", "8": "5.5", "9": "6", "10": "7" } } }, { upsert: true });
print("✅ Upserted conversionRules:", dbx.conversionRules.countDocuments());

const sub_f3386c57_92f3_4c6c_a587_adacff373e29 = ObjectId("5d551bc446d09ae6dfd2d4cf");
const sub_86e04064_e252_4ce3_92cf_738d9002183b = ObjectId("d8f720d8dbaebf20e564e60c");
const sub_b06718d4_9b3b_4637_a13f_f4235ee9dbfc = ObjectId("0a5c95ef0e6abd9b0f98b264");
const sub_f9e5dc0c_ae82_4e53_99af_bcdb3343809f = ObjectId("78e883d706106884ad8d46a7");
const sub_08f9828b_62e9_4094_b930_f23ea4632ea9 = ObjectId("af135c7ca9c1d71355daaf73");
const sub_1f0f78a9_a7a8_4e99_9ffd_0f01dea52124 = ObjectId("849677da41adcd992dabb351");
const sub_f76adb39_b9f2_4855_9462_026aca2ef7a9 = ObjectId("81898155ca52f117852393eb");
const sub_894860bc_ccb4_4e75_a001_8d0151e87337 = ObjectId("419c80e3bfe5982d360b8d7e");
const sub_f059eeb1_e3fe_4a0d_a260_b5cfc4e1ffad = ObjectId("1691aa15e1093d9795fa455a");
const sub_c9a0c40e_7a7b_4f9d_b666_4d5e3d25babc = ObjectId("d48dafb0ab3502b95146a6b7");
const sub_3b1c74b3_d445_4c59_8fae_b8ede8c1c433 = ObjectId("a987a877306067fe7da9de60");
const sub_6147060c_5371_441f_8124_03eb8ed6db20 = ObjectId("b429b8b53843ff4098559826");
const sub_e492a494_cc4b_446b_a2cb_83f77b1639b5 = ObjectId("5d4e899957c8cd1910641221");
const sub_a5b9e7ad_3d6f_41bc_acc1_cbd9be9f43e4 = ObjectId("e4fcd315d473a40c5ad5d54e");
dbx.subjects.insertMany([
  { _id: ObjectId("5d551bc446d09ae6dfd2d4cf"), neo4jId: "f3386c57-92f3-4c6c-a587-adacff373e29", name: "Matemática I", institutionId: inst_uba, country: "ARG", levelStage: "19" },
  { _id: ObjectId("d8f720d8dbaebf20e564e60c"), neo4jId: "86e04064-e252-4ce3-92cf-738d9002183b", name: "Matemática II", institutionId: inst_uba, country: "ARG", levelStage: "19" },
  { _id: ObjectId("0a5c95ef0e6abd9b0f98b264"), neo4jId: "b06718d4-9b3b-4637-a13f-f4235ee9dbfc", name: "Programación I", institutionId: inst_uba, country: "ARG", levelStage: "19" },
  { _id: ObjectId("78e883d706106884ad8d46a7"), neo4jId: "f9e5dc0c-ae82-4e53-99af-bcdb3343809f", name: "Economía", institutionId: inst_uba, country: "ARG", levelStage: "19" },
  { _id: ObjectId("af135c7ca9c1d71355daaf73"), neo4jId: "08f9828b-62e9-4094-b930-f23ea4632ea9", name: "Matemática I", institutionId: inst_uade, country: "ARG", levelStage: "19" },
  { _id: ObjectId("849677da41adcd992dabb351"), neo4jId: "1f0f78a9-a7a8-4e99-9ffd-0f01dea52124", name: "Matemática II", institutionId: inst_uade, country: "ARG", levelStage: "19" },
  { _id: ObjectId("81898155ca52f117852393eb"), neo4jId: "f76adb39-b9f2-4855-9462-026aca2ef7a9", name: "Programación I", institutionId: inst_uade, country: "ARG", levelStage: "19" },
  { _id: ObjectId("419c80e3bfe5982d360b8d7e"), neo4jId: "894860bc-ccb4-4e75-a001-8d0151e87337", name: "Base de Datos", institutionId: inst_uade, country: "ARG", levelStage: "19" },
  { _id: ObjectId("1691aa15e1093d9795fa455a"), neo4jId: "f059eeb1-e3fe-4a0d-a260-b5cfc4e1ffad", name: "Mathematics I", institutionId: inst_uk_inst, country: "UK", levelStage: "19" },
  { _id: ObjectId("d48dafb0ab3502b95146a6b7"), neo4jId: "c9a0c40e-7a7b-4f9d-b666-4d5e3d25babc", name: "Programming I", institutionId: inst_uk_inst, country: "UK", levelStage: "19" },
  { _id: ObjectId("a987a877306067fe7da9de60"), neo4jId: "3b1c74b3-d445-4c59-8fae-b8ede8c1c433", name: "Economics", institutionId: inst_uk_inst, country: "UK", levelStage: "19" },
  { _id: ObjectId("b429b8b53843ff4098559826"), neo4jId: "6147060c-5371-441f-8124-03eb8ed6db20", name: "Calculus I", institutionId: inst_us_inst, country: "US", levelStage: "19" },
  { _id: ObjectId("5d4e899957c8cd1910641221"), neo4jId: "e492a494-cc4b-446b-a2cb-83f77b1639b5", name: "Intro to Programming", institutionId: inst_us_inst, country: "US", levelStage: "19" },
  { _id: ObjectId("e4fcd315d473a40c5ad5d54e"), neo4jId: "a5b9e7ad-3d6f-41bc-acc1-cbd9be9f43e4", name: "Microeconomics", institutionId: inst_us_inst, country: "US", levelStage: "19" },
]);
print("✅ Inserted subjects:", dbx.subjects.countDocuments());

dbx.grades.insertMany([
  { subjectId: "5d551bc446d09ae6dfd2d4cf", studentId: "76c23cb6d9834dc12a9e2f14", institutionId: "501b6ff69b36d251d142e796", name: "Matemática I - Examen 2", system: "AR_1_10", type: "exam", country: "ARG", grade: "19", date: new Date("2018-04-19T00:00:00.000Z"), value: "2" },
  { subjectId: "5d551bc446d09ae6dfd2d4cf", studentId: "76c23cb6d9834dc12a9e2f14", institutionId: "501b6ff69b36d251d142e796", name: "Matemática I - Examen 1", system: "AR_1_10", type: "exam", country: "ARG", grade: "19", date: new Date("2018-08-02T00:00:00.000Z"), value: "7" },
  { subjectId: "d8f720d8dbaebf20e564e60c", studentId: "76c23cb6d9834dc12a9e2f14", institutionId: "501b6ff69b36d251d142e796", name: "Matemática II - Examen 1", system: "AR_1_10", type: "exam", country: "ARG", grade: "19", date: new Date("2019-03-10T00:00:00.000Z"), value: "10" },
  { subjectId: "0a5c95ef0e6abd9b0f98b264", studentId: "76c23cb6d9834dc12a9e2f14", institutionId: "501b6ff69b36d251d142e796", name: "Programación I - Examen 1", system: "AR_1_10", type: "exam", country: "ARG", grade: "19", date: new Date("2019-08-02T00:00:00.000Z"), value: "4" },
  { subjectId: "81898155ca52f117852393eb", studentId: "76c23cb6d9834dc12a9e2f14", institutionId: "6aa06d4942ac05800eb4b57f", name: "Programación I - Examen 1", system: "AR_1_10", type: "exam", country: "ARG", grade: "19", date: new Date("2022-06-30T00:00:00.000Z"), value: "10" },
  { subjectId: "849677da41adcd992dabb351", studentId: "76c23cb6d9834dc12a9e2f14", institutionId: "6aa06d4942ac05800eb4b57f", name: "Matemática II - Examen 1", system: "AR_1_10", type: "exam", country: "ARG", grade: "19", date: new Date("2022-07-22T00:00:00.000Z"), value: "4" },
  { subjectId: "af135c7ca9c1d71355daaf73", studentId: "76c23cb6d9834dc12a9e2f14", institutionId: "6aa06d4942ac05800eb4b57f", name: "Matemática I - Examen 1", system: "AR_1_10", type: "exam", country: "ARG", grade: "19", date: new Date("2022-08-24T00:00:00.000Z"), value: "7" },
  { subjectId: "849677da41adcd992dabb351", studentId: "76c23cb6d9834dc12a9e2f14", institutionId: "6aa06d4942ac05800eb4b57f", name: "Matemática II - Examen 2", system: "AR_1_10", type: "exam", country: "ARG", grade: "19", date: new Date("2022-09-02T00:00:00.000Z"), value: "9" },
  { subjectId: "81898155ca52f117852393eb", studentId: "76c23cb6d9834dc12a9e2f14", institutionId: "6aa06d4942ac05800eb4b57f", name: "Programación I - Examen 2", system: "AR_1_10", type: "exam", country: "ARG", grade: "19", date: new Date("2022-11-09T00:00:00.000Z"), value: "4" },
  { subjectId: "419c80e3bfe5982d360b8d7e", studentId: "76c23cb6d9834dc12a9e2f14", institutionId: "6aa06d4942ac05800eb4b57f", name: "Base de Datos - Examen 1", system: "AR_1_10", type: "exam", country: "ARG", grade: "19", date: new Date("2025-05-25T00:00:00.000Z"), value: "10" },
  {
    subjectId: "81898155ca52f117852393eb",
    studentId: "5f1d7f3e8b9c4a1a2b3c4d5e",
    institutionId: "6aa06d4942ac05800eb4b57f",
    name: "Programación I - Examen 1",
    system: "AR_1_10",
    type: "exam",
    country: "ARG",
    grade: "19",
    date: new Date("2022-06-30T00:00:00.000Z"),
    value: "8"
  },
  {
    subjectId: "af135c7ca9c1d71355daaf73",
    studentId: "5f1d7f3e8b9c4a1a2b3c4d5e",
    institutionId: "6aa06d4942ac05800eb4b57f",
    name: "Matemática I - Examen 1",
    system: "AR_1_10",
    type: "exam",
    country: "ARG",
    grade: "19",
    date: new Date("2022-08-24T00:00:00.000Z"),
    value: "6"
  },

  {
    subjectId: "419c80e3bfe5982d360b8d7e",
    studentId: "5f1d7f3e8b9c4a1a2b3c4d5e",
    institutionId: "6aa06d4942ac05800eb4b57f",
    name: "Base de Datos - Examen 1",
    system: "AR_1_10",
    type: "exam",
    country: "ARG",
    grade: "19",
    date: new Date("2025-05-25T00:00:00.000Z"),
    value: "7"
  },
  {
    subjectId: "81898155ca52f117852393eb",
    studentId: "5f1d7f3e8b9c4a1a2b3c4d5e",
    institutionId: "6aa06d4942ac05800eb4b57f",
    name: "Programación I - Examen 2",
    system: "AR_1_10",
    type: "exam",
    country: "ARG",
    grade: "19",
    date: new Date("2022-07-30T00:00:00.000Z"),
    value: "9"
  },
  {
    subjectId: "849677da41adcd992dabb351",
    studentId: "5f1d7f3e8b9c4a1a2b3c4d5e",
    institutionId: "6aa06d4942ac05800eb4b57f",
    name: "Matemática II - Examen 1",
    system: "AR_1_10",
    type: "exam",
    country: "ARG",
    grade: "19",
    date: new Date("2022-09-15T00:00:00.000Z"),
    value: "5"
  },
  {
    subjectId: "419c80e3bfe5982d360b8d7e",
    studentId: "5f1d7f3e8b9c4a1a2b3c4d5e",
    institutionId: "6aa06d4942ac05800eb4b57f",
    name: "Base de Datos - Examen 2",
    system: "AR_1_10",
    type: "exam",
    country: "ARG",
    grade: "19",
    date: new Date("2023-02-10T00:00:00.000Z"),
    value: "8"
  },
]);

print("✅ Inserted grades:", dbx.grades.countDocuments());
print("✅ Seed completed successfully");
