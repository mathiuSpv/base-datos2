/* eslint-disable no-undef */
print("🌱 Seeding MongoDB (minimal, aligned with Neo4j)...");
const dbx = db.getSiblingDB("edugrade");
dbx.dropDatabase();
print("✅ Dropped database edugrade");


const inst_chl_secondary = ObjectId("c549bc38c0614170f01a2fef");
const inst_arg_secondary = ObjectId("d2f1e3a4b5c67890abcdef12");
const inst_uba = ObjectId("501b6ff69b36d251d142e796");
const inst_uade = ObjectId("6aa06d4942ac05800eb4b57f");
const inst_uk_inst = ObjectId("07cc736e090e75966d562a9b");
const inst_us_inst = ObjectId("1cd767efc7bae3e6bd19574d");
const inst_de_inst = ObjectId("9802a6b16aba871af182b6cb");

dbx.institutions.insertMany([
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
dbx.options.insertOne({
  key: "system",
  response: {
    "GBR": [
      "GBR_ASTAR_F",
      "GBR_GCSE",
      "GBR_ALEVEL"
    ],
    "USA": [
      "USA_LETTER_A_F",
      "USA_GPA_0_4"
    ],
    "DEU": [
      "DEU_1_6_INVERTED"
    ],
    "ARG": [
      "ARG_1_10"
    ]
  }
})
print("✅ Upserted options");

dbx.conversionRules.updateOne(
  { system: "ARG_1_10", country: "ARG", grade: "12", validFrom: ISODate("2020-01-01T00:00:00.000Z") },
  {
    $set: {
      system: "ARG_1_10",
      country: "ARG",
      grade: { min: "0", max: "99" },
      validFrom: ISODate("2020-01-01T00:00:00.000Z"),
      validTo: null,

      map: {
        "1": "1",
        "2": "1.5",
        "3": "2",
        "4": "2.5",
        "5": "3",
        "6": "4",
        "7": "5",
        "8": "5.5",
        "9": "6",
        "10": "7"
      }
    }
  },
  { upsert: true }
);
print("✅ Upserted conversionRules:", dbx.conversionRules.countDocuments());
print("✅ Seed completed successfully");
