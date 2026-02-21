db = db.getSiblingDB("edugrade");

db.options.updateOne(
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

db.conversionRules.updateOne(
  { system: "AR_1_10", country: "ARG", grade: "12", validFrom: ISODate("2020-01-01T00:00:00.000Z") },
  {
    $set: {
      system: "AR_1_10",
      country: "ARG",
      grade: "12",

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

console.log("Seed completed successfully");