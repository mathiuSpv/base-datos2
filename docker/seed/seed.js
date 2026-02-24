/* eslint-disable no-undef */
print("🌱 Seeding MongoDB (ZA pivot rules)...");
const dbx = db.getSiblingDB("edugrade");
dbx.dropDatabase();
print("✅ Dropped database edugrade");

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
        "25": "Doctoral Degree (PhD)",
      },
    },
  },
  { upsert: true }
);

dbx.options.updateOne(
  { key: "system" },
  {
    $set: {
      key: "system",
      response: {
        "GBR": ["GBR_ASTAR_F", "GBR_GCSE", "GBR_ALEVEL"],
        "USA": ["USA_LETTER_A_F", "USA_GPA_0_4"],
        "DEU": ["DEU_1_6_INVERTED"],
        "ARG": ["ARG_1_10"],
        "ZAF": ["ZA"],
      },
    },
  },
  { upsert: true }
);

dbx.options.updateOne(
  { key: "country" },
  {
    $set: {
      key: "country",
      response: {
        "ZAF": "South Africa",
        "GBR": "United Kingdom",
        "USA": "United States of America",
        "DEU": "Germany",
        "ARG": "Argentina",
      },
    },
  },
  { upsert: true }
);

print("✅ Upserted options");

const validFrom = ISODate("2000-01-01T00:00:00.000Z");
const createdAt = new Date();
const gradeRange = { min: "0", max: "99" };

dbx.conversionRules.insertMany([
  { direction: "TO_ZA", system: "ARG_1_10", country: "ANY", grade: gradeRange, validFrom, validTo: null, createdAt, map: { "1": "1", "2": "1.5", "3": "2", "4": "2.5", "5": "3", "6": "4", "7": "5", "8": "5.5", "9": "6", "10": "7" } },
  { direction: "TO_ZA", system: "USA_GPA_0_4", country: "ANY", grade: gradeRange, validFrom, validTo: null, createdAt, map: { "4.0": "7", "3.7": "6.5", "3.3": "6", "3.0": "5.5", "2.7": "5", "2.3": "4.5", "2.0": "4", "1.7": "3.5", "1.3": "3", "1.0": "2.5", "0.0": "1" } },
  { direction: "TO_ZA", system: "USA_LETTER_A_F", country: "ANY", grade: gradeRange, validFrom, validTo: null, createdAt, map: { "A": "7", "A-": "6.5", "B+": "6", "B": "5.5", "B-": "5", "C+": "4.5", "C": "4", "C-": "3.5", "D+": "3", "D": "2.5", "D-": "2", "F": "1" } },
  { direction: "TO_ZA", system: "DEU_1_6_INVERTED", country: "ANY", grade: gradeRange, validFrom, validTo: null, createdAt, map: { "1.0": "7", "1.3": "6.5", "1.7": "6", "2.0": "5.5", "2.3": "5", "2.7": "4.5", "3.0": "4", "3.3": "3.5", "3.7": "3", "4.0": "2.5", "4.3": "2", "4.7": "1.5", "5.0": "1", "6.0": "0.5" } },
  { direction: "TO_ZA", system: "GBR_ALEVEL", country: "ANY", grade: gradeRange, validFrom, validTo: null, createdAt, map: { "A*": "7", "A": "6.5", "B": "6", "C": "5", "D": "4", "E": "3", "U": "1" } },
  { direction: "TO_ZA", system: "GBR_GCSE", country: "ANY", grade: gradeRange, validFrom, validTo: null, createdAt, map: { "1": "2", "2": "2.5", "3": "3", "4": "4", "5": "5", "6": "5.5", "7": "6", "8": "6.5", "9": "7", "U": "1" } },
  { direction: "TO_ZA", system: "GBR_ASTAR_F", country: "ANY", grade: gradeRange, validFrom, validTo: null, createdAt, map: { "A*": "7", "A": "6.5", "B": "6", "C": "5", "D": "4", "E": "3", "F": "2", "U": "1" } },

  { direction: "FROM_ZA", system: "ARG_1_10", country: "ANY", grade: gradeRange, validFrom, validTo: null, createdAt, map: { "1": "1", "1.5": "2", "2": "3", "2.5": "4", "3": "5", "4": "6", "5": "7", "5.5": "8", "6": "9", "7": "10" } },
  { direction: "FROM_ZA", system: "USA_GPA_0_4", country: "ANY", grade: gradeRange, validFrom, validTo: null, createdAt, map: { "7": "4.0", "6.5": "3.7", "6": "3.3", "5.5": "3.0", "5": "2.7", "4.5": "2.3", "4": "2.0", "3.5": "1.7", "3": "1.3", "2.5": "1.0", "1": "0.0" } },
  { direction: "FROM_ZA", system: "USA_LETTER_A_F", country: "ANY", grade: gradeRange, validFrom, validTo: null, createdAt, map: { "7": "A", "6.5": "A-", "6": "B+", "5.5": "B", "5": "B-", "4.5": "C+", "4": "C", "3.5": "C-", "3": "D+", "2.5": "D", "2": "D-", "1": "F" } },
  { direction: "FROM_ZA", system: "DEU_1_6_INVERTED", country: "ANY", grade: gradeRange, validFrom, validTo: null, createdAt, map: { "7": "1.0", "6.5": "1.3", "6": "1.7", "5.5": "2.0", "5": "2.3", "4.5": "2.7", "4": "3.0", "3.5": "3.3", "3": "3.7", "2.5": "4.0", "2": "4.3", "1.5": "4.7", "1": "5.0", "0.5": "6.0" } },
  { direction: "FROM_ZA", system: "GBR_ALEVEL", country: "ANY", grade: gradeRange, validFrom, validTo: null, createdAt, map: { "7": "A*", "6.5": "A", "6": "B", "5": "C", "4": "D", "3": "E", "1": "U" } },
  { direction: "FROM_ZA", system: "GBR_GCSE", country: "ANY", grade: gradeRange, validFrom, validTo: null, createdAt, map: { "2": "1", "2.5": "2", "3": "3", "4": "4", "5": "5", "5.5": "6", "6": "7", "6.5": "8", "7": "9", "1": "U" } },
  { direction: "FROM_ZA", system: "GBR_ASTAR_F", country: "ANY", grade: gradeRange, validFrom, validTo: null, createdAt, map: { "7": "A*", "6.5": "A", "6": "B", "5": "C", "4": "D", "3": "E", "2": "F", "1": "U" } },
]);

print("✅ Inserted conversionRules:", dbx.conversionRules.countDocuments());
print("✅ Seed completed successfully");