MATCH (n) DETACH DELETE n;

// Constraints (idempotent) - same as backend ensures
CREATE CONSTRAINT student_mongoId IF NOT EXISTS FOR (s:Student) REQUIRE s.mongoId IS UNIQUE;
CREATE CONSTRAINT institution_mongoId IF NOT EXISTS FOR (i:Institution) REQUIRE i.mongoId IS UNIQUE;
CREATE CONSTRAINT subject_id IF NOT EXISTS FOR (sub:Subject) REQUIRE sub.id IS UNIQUE;
CREATE CONSTRAINT subject_unique IF NOT EXISTS FOR (sub:Subject) REQUIRE (sub.name, sub.institutionMongoId) IS UNIQUE;

CREATE (:Institution {mongoId: "d2f1e3a4b5c67890abcdef12"});
CREATE (:Institution {mongoId: "c549bc38c0614170f01a2fef"});
CREATE (:Institution {mongoId: "501b6ff69b36d251d142e796"});
CREATE (:Institution {mongoId: "6aa06d4942ac05800eb4b57f"});
CREATE (:Institution {mongoId: "07cc736e090e75966d562a9b"});
CREATE (:Institution {mongoId: "1cd767efc7bae3e6bd19574d"});
CREATE (:Institution {mongoId: "9802a6b16aba871af182b6cb"});

// Subjects
CREATE (:Subject {id:"f3386c57-92f3-4c6c-a587-adacff373e29", name:"Matemática I", institutionMongoId:"501b6ff69b36d251d142e796"});
CREATE (:Subject {id:"86e04064-e252-4ce3-92cf-738d9002183b", name:"Matemática II", institutionMongoId:"501b6ff69b36d251d142e796"});
CREATE (:Subject {id:"b06718d4-9b3b-4637-a13f-f4235ee9dbfc", name:"Programación I", institutionMongoId:"501b6ff69b36d251d142e796"});
CREATE (:Subject {id:"08f9828b-62e9-4094-b930-f23ea4632ea9", name:"Matemática I", institutionMongoId:"6aa06d4942ac05800eb4b57f"});
CREATE (:Subject {id:"1f0f78a9-a7a8-4e99-9ffd-0f01dea52124", name:"Matemática II", institutionMongoId:"6aa06d4942ac05800eb4b57f"});
CREATE (:Subject {id:"f76adb39-b9f2-4855-9462-026aca2ef7a9", name:"Programación I", institutionMongoId:"6aa06d4942ac05800eb4b57f"});
CREATE (:Subject {id:"894860bc-ccb4-4e75-a001-8d0151e87337", name:"Base de Datos", institutionMongoId:"6aa06d4942ac05800eb4b57f"});
CREATE (:Subject {id:"f9e5dc0c-ae82-4e53-99af-bcdb3343809f", name:"Economía", institutionMongoId:"501b6ff69b36d251d142e796"});
CREATE (:Subject {id:"f059eeb1-e3fe-4a0d-a260-b5cfc4e1ffad", name:"Mathematics I", institutionMongoId:"07cc736e090e75966d562a9b"});
CREATE (:Subject {id:"c9a0c40e-7a7b-4f9d-b666-4d5e3d25babc", name:"Programming I", institutionMongoId:"07cc736e090e75966d562a9b"});
CREATE (:Subject {id:"3b1c74b3-d445-4c59-8fae-b8ede8c1c433", name:"Economics", institutionMongoId:"07cc736e090e75966d562a9b"});
CREATE (:Subject {id:"6147060c-5371-441f-8124-03eb8ed6db20", name:"Calculus I", institutionMongoId:"1cd767efc7bae3e6bd19574d"});
CREATE (:Subject {id:"e492a494-cc4b-446b-a2cb-83f77b1639b5", name:"Intro to Programming", institutionMongoId:"1cd767efc7bae3e6bd19574d"});
CREATE (:Subject {id:"a5b9e7ad-3d6f-41bc-acc1-cbd9be9f43e4", name:"Microeconomics", institutionMongoId:"1cd767efc7bae3e6bd19574d"});