#!/usr/bin/env python3
"""
EduGrade Global – API caller / seeder (v2)

Orden (como pediste):
1) Alta de alumno (AMOUNT_STUDENT +/- jitter)
2) Alta de instituciones (AMOUNT_INSTITUTIONS +/- jitter) -> luego GET list para guardar ids
3) Alta relación alumno - institución (min 1, max 3; hasta 2 casos con solapamiento)
4) Alta de materias en institución (AMOUNT_SUBJECTS +/- jitter; distribución NO equitativa)
5) Cargar notas/exams (AMOUNT_EXAMS +/- jitter) con estudiante + institución + materia

⚠️ Importante:
- SOLO usa endpoints HTTP (no toca DB directo), para respetar Neo4j + MongoDB.
- Base URL típica: http://localhost:8000

Uso:
  python api_caller_seed.py --base-url http://localhost:8000 --seed 123

Requisitos:
  pip install httpx
"""

from __future__ import annotations

import argparse
import math
import random
import string
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx


# ============================================================
#  Ajustes principales (base) + jitter "con sentido"
# ============================================================
AMOUNT_STUDENT = 30
AMOUNT_INSTITUTIONS = 10
AMOUNT_SUBJECTS = 300
AMOUNT_EXAMS = 500

# cuánto puede variar cada cantidad respecto del base (ej. 0.25 = ±25%)
JITTER = {
  "students": 0.20,
  "institutions": 0.25,
  "subjects": 0.15,
  "exams": 0.20,
}


# ============================================================
#  Country ISO-3 permitido + sistemas por país (materias/exams)
# ============================================================
COUNTRIES_ISO3 = {
  "ZAF": "South Africa",
  "GBR": "United Kingdom",
  "USA": "United States of America",
  "DEU": "Germany",
  "ARG": "Argentina",
}

SYSTEMS_BY_COUNTRY = {
  "GBR": ["GBR_ASTAR_F", "GBR_GCSE", "GBR_ALEVEL"],
  "USA": ["USA_LETTER_A_F", "USA_GPA_0_4"],
  "DEU": ["DEU_1_6_INVERTED"],
  "ARG": ["ARG_1_10"],
  "ZAF": ["ZA"],
}
NATIONALITIES = [
  "Argentine",
  "South African",
  "British",
  "American",
  "German",
  "Uruguayan",
  "Chilean",
  "Paraguayan",
  "Bolivian",
  "Peruvian",
  "Colombian",
  "Mexican",
  "Spanish",
  "Brazilian",
  "Canadian",
  "Australian",
  "New Zealander",
  "French",
  "Italian",
  "Portuguese",
  "Dutch",
  "Swiss",
  "Swedish",
  "Norwegian",
  "Danish",
  "Finnish",
  "Irish",
  "Scottish",
  "Welsh",
  "Indian",
  "Chinese",
  "Japanese",
  "South Korean"
]

valueExams = {
    "ARG_1_10": ["1","2","3","4","5","6","7","8","9","10"],

    "USA_GPA_0_4": ["4.0","3.7","3.3","3.0","2.7","2.3","2.0","1.7","1.3","1.0","0.0"],

    "USA_LETTER_A_F": ["A","A-","B+","B","B-","C+","C","C-","D+","D","D-","F"],

    "DEU_1_6_INVERTED": [
      "1.0","1.3","1.7","2.0","2.3","2.7",
      "3.0","3.3","3.7","4.0","4.3","4.7","5.0","6.0"
    ],

    "GBR_ALEVEL": ["A*","A","B","C","D","E","U"],

    "GBR_GCSE": ["1","2","3","4","5","6","7","8","9","U"],

    "GBR_ASTAR_F": ["A*","A","B","C","D","E","F","U"],

    # escala ZA (por si algún system es ZA)
    "ZA": ["1","1.5","2","2.5","3","3.5","4","4.5","5","5.5","6","6.5","7"]
}


# ----------------------------
# Random helpers
# ----------------------------
FIRST_NAMES = [
  "Sofía","Mateo","Valentina","Benjamín","Martina","Thiago","Emma","Joaquín","Catalina","Tomás",
  "Camila","Lautaro","Abril","Santiago","Lucía","Franco","Milagros","Nicolás","Agustina","Juan",
]
LAST_NAMES = [
  "García","González","Rodríguez","López","Martínez","Pérez","Sánchez","Romero","Díaz","Fernández",
  "Torres","Gómez","Flores","Herrera","Vargas","Castro","Silva","Ramos","Acosta","Medina",
]
INSTITUTION_SUFFIX = ["Institute", "College", "Universidad", "Escuela", "Academia"]
STREET = ["Av. Siempre Viva", "Calle Mitre", "Av. Rivadavia", "Calle San Martín", "Av. Libertador", "Calle Belgrano"]
EXAM_TYPES = ["Parcial", "Final", "TP", "Quiz", "Recuperatorio"]
GRADE_LABELS = [
  "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
  "11", "12", "13", "14", "15", "16", "17", "18",
  "19", "20", "21", "22"
]
SUBJECT_WORDS = ["Álgebra","Historia","Química","Programación","Física","Geografía","Literatura","Biología","Economía","Estadística","Cálculo","Redes","Bases de Datos","IA","Sistemas Operativos","Derecho","Filosofía","Psicología","Marketing","Finanzas"]


def rchoice(xs):
  return xs[random.randrange(len(xs))]


def rand_identity() -> str:
  letters = "".join(random.choice(string.ascii_uppercase) for _ in range(2))
  digits = "".join(random.choice(string.digits) for _ in range(5))
  return f"AR-{letters}{digits}"


def rand_birthdate(min_age: int = 16, max_age: int = 28) -> date:
  today = date.today()
  age = random.randint(min_age, max_age)
  offset = random.randint(-180, 180)
  return today - timedelta(days=age * 365 + offset)


def rand_date_between(d1: date, d2: date) -> date:
  if d2 < d1:
    d1, d2 = d2, d1
  span = (d2 - d1).days
  return d1 + timedelta(days=random.randint(0, max(0, span)))


def iso(d: Optional[date]) -> Optional[str]:
  return None if d is None else d.isoformat()


def jitter_amount(base: int, key: str, min_value: int = 1) -> int:
  """
  Devuelve una cantidad random alrededor de un base con jitter.
  Se estabiliza con --seed.
  """
  j = JITTER.get(key, 0.0)
  lo = max(min_value, int(math.floor(base * (1 - j))))
  hi = max(min_value, int(math.ceil(base * (1 + j))))
  if hi < lo:
    hi = lo
  return random.randint(lo, hi)


# ----------------------------
# HTTP client wrapper
# ----------------------------
@dataclass
class Api:
  base_url: str
  timeout_s: float = 30.0

  def __post_init__(self):
    self.client = httpx.Client(base_url=self.base_url.rstrip("/"), timeout=self.timeout_s)

  def close(self):
    self.client.close()

  # ---- Students ----
  def create_student(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    r = self.client.post("/api/students", json=payload)
    r.raise_for_status()
    return r.json()

  def link_student_institution(self, student_id: str, institution_id: str, start: str, end: Optional[str]) -> None:
    params = {"institution_id": institution_id, "start": start}
    if end is not None:
      params["end"] = end
    r = self.client.post(f"/api/students/{student_id}/institution", params=params)
    r.raise_for_status()

  def link_student_subject(self, student_id: str, subject_id: str, start: str, grade: str, end: Optional[str]) -> None:
    params = {"subject_id": subject_id, "start": start, "grade": grade}
    if end is not None:
      params["end"] = end
    r = self.client.post(f"/api/students/{student_id}/subject", params=params)
    r.raise_for_status()

  # ---- Institutions ----
  def list_institutions(self, limit: int = 500, skip: int = 0) -> List[Dict[str, Any]]:
    r = self.client.get("/api/institutions", params={"limit": limit, "skip": skip})
    r.raise_for_status()
    return r.json()

  def create_institution(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    r = self.client.post("/api/institutions", json=payload)
    r.raise_for_status()
    return r.json()

  # ---- Subjects ----
  def create_subject_for_institution(self, institution_id: str, name: str) -> Dict[str, Any]:
    r = self.client.post(f"/api/institutions/{institution_id}/subjects", params={"name": name})
    r.raise_for_status()
    return r.json()

  # ---- Exams ----
  def create_exam(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    print(payload)
    r = self.client.post("/api/exams", json=payload)
    r.raise_for_status()
    return r.json()


# ----------------------------
# Payload builders
# ----------------------------
def make_random_student_payload() -> Dict[str, Any]:
  first = rchoice(FIRST_NAMES)
  last = rchoice(LAST_NAMES)
  nationality = random.choice(NATIONALITIES)
  payload = {
    "identity": rand_identity() if random.random() < 0.8 else None,
    "firstName": first,
    "lastName": last,
    "birthDate": rand_birthdate().isoformat(),
    "nationality": nationality,
  }
  return {k: v for k, v in payload.items() if v is not None}


def make_random_institution_payload(i: int) -> Dict[str, Any]:
  country = random.choice(list(COUNTRIES_ISO3.keys()))  # ISO-3
  name = f"{rchoice(INSTITUTION_SUFFIX)} {rchoice(LAST_NAMES)} {i+1}"
  address = f"{rchoice(STREET)} {random.randint(100, 9999)}, {COUNTRIES_ISO3[country]}"
  return {"name": name, "country": country, "address": address}


def make_subject_name(inst_idx: int, subj_idx: int) -> str:
  base = f"{rchoice(SUBJECT_WORDS)} {inst_idx+1}-{subj_idx+1}"
  return base[:50]


# ----------------------------
# Relationship generation
# ----------------------------
def build_student_institution_periods(
  student_count: int,
  inst_ids: List[str],
  max_overlap_cases: int = 2,
) -> List[List[Tuple[str, date, Optional[date]]]]:
  if not inst_ids:
    raise ValueError("No hay instituciones para relacionar.")

  today = date.today()
  overlap_students = set(random.sample(range(student_count), k=min(max_overlap_cases, student_count)))

  all_periods: List[List[Tuple[str, date, Optional[date]]]] = []
  for sid in range(student_count):
    k = random.randint(1, min(3, len(inst_ids)))
    chosen = random.sample(inst_ids, k=k)

    periods: List[Tuple[str, date, Optional[date]]] = []

    base_start = today - timedelta(days=random.randint(365 * 6, 365 * 10))
    cursor = base_start

    if sid in overlap_students and k >= 2:
      inst0, inst1 = chosen[0], chosen[1]
      start0 = cursor
      dur0 = timedelta(days=random.randint(250, 800))
      end0 = start0 + dur0

      start1 = start0 + timedelta(days=random.randint(90, max(91, dur0.days - 90)))
      dur1 = timedelta(days=random.randint(250, 800))
      end1 = start1 + dur1

      end0_out: Optional[date] = end0 if random.random() < 0.85 else None
      end1_out: Optional[date] = end1 if random.random() < 0.85 else None

      periods.append((inst0, start0, end0_out))
      periods.append((inst1, start1, end1_out))

      cursor = max(end0, end1) + timedelta(days=random.randint(30, 120))

      if k == 3:
        inst2 = chosen[2]
        start2 = cursor
        end2 = start2 + timedelta(days=random.randint(250, 900))
        end2_out: Optional[date] = end2 if random.random() < 0.8 else None
        periods.append((inst2, start2, end2_out))
    else:
      for inst in chosen:
        start = cursor
        end = start + timedelta(days=random.randint(250, 900))
        end_out: Optional[date] = end if random.random() < 0.85 else None
        periods.append((inst, start, end_out))
        cursor = end + timedelta(days=random.randint(30, 180))

    all_periods.append(periods)

  return all_periods


def uneven_split(total: int, n: int) -> List[int]:
  if n <= 0:
    return []
  if total < n:
    sizes = [0] * n
    for i in range(total):
      sizes[i] = 1
    random.shuffle(sizes)
    return sizes

  weights = [random.random() ** 2 for _ in range(n)]
  s = sum(weights)
  raw = [w / s * total for w in weights]
  sizes = [max(1, int(x)) for x in raw]

  diff = total - sum(sizes)
  while diff != 0:
    i = random.randrange(n)
    if diff > 0:
      sizes[i] += 1
      diff -= 1
    else:
      if sizes[i] > 1:
        sizes[i] -= 1
        diff += 1
  return sizes


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--base-url", required=True, help="Ej: http://localhost:8000")
  ap.add_argument("--seed", type=int, default=None, help="Seed para reproducibilidad")
  args = ap.parse_args()

  if args.seed is not None:
    random.seed(args.seed)

  n_students = jitter_amount(AMOUNT_STUDENT, "students", min_value=1)
  n_institutions = jitter_amount(AMOUNT_INSTITUTIONS, "institutions", min_value=1)
  n_subjects_total = jitter_amount(AMOUNT_SUBJECTS, "subjects", min_value=max(1, n_institutions))
  n_exams_total = jitter_amount(AMOUNT_EXAMS, "exams", min_value=n_students)

  api = Api(args.base_url)

  try:
    print("=== Parámetros efectivos (con jitter) ===")
    print(f"- students:      {n_students} (base {AMOUNT_STUDENT})")
    print(f"- institutions:  {n_institutions} (base {AMOUNT_INSTITUTIONS})")
    print(f"- subjects:      {n_subjects_total} (base {AMOUNT_SUBJECTS})")
    print(f"- exams:         {n_exams_total} (base {AMOUNT_EXAMS})")

    print("\n1) Alta de alumnos")
    students: List[Dict[str, Any]] = []
    for i in range(n_students):
      s = api.create_student(make_random_student_payload())
      students.append(s)
      print(f"  - student[{i}] _id={s.get('_id')} {s.get('firstName')} {s.get('lastName')}")

    print("\n2) Alta de instituciones (NOSOTROS) + GET list")
    created_insts: List[Dict[str, Any]] = []
    for i in range(n_institutions):
      inst = api.create_institution(make_random_institution_payload(i))
      created_insts.append(inst)
      print(f"  - institution[{i}] _id={inst.get('_id')} country={inst.get('country')} name={inst.get('name')}")

    # guardamos IDs de las que creamos (sin chequear existentes)
    inst_ids = [str(x.get("_id") or x.get("id")) for x in created_insts]
    inst_by_id = {str(x.get("_id") or x.get("id")): x for x in created_insts}
    print(f"  - instituciones creadas para este seed: {len(inst_ids)}")

    print("\n3) Alta rel alumno–institución (min 1, max 3; hasta 2 solapes)")
    periods_by_student = build_student_institution_periods(
      student_count=len(students),
      inst_ids=inst_ids,
      max_overlap_cases=2,
    )

    student_inst_map: Dict[str, List[Tuple[str, date, Optional[date]]]] = {}
    for i, s in enumerate(students):
      sid = str(s.get("_id") or s.get("id"))
      student_inst_map[sid] = periods_by_student[i]
      for (inst_id, start_d, end_d) in periods_by_student[i]:
        api.link_student_institution(
          student_id=sid,
          institution_id=inst_id,
          start=iso(start_d),
          end=iso(end_d),
        )
      print(f"  - student[{i}] {sid}: {len(periods_by_student[i])} instituciones")

    print("\n4) Alta de materias en institución (distribución NO equitativa)")
    counts = uneven_split(n_subjects_total, len(inst_ids))
    subjects_by_inst: Dict[str, List[Dict[str, Any]]] = {iid: [] for iid in inst_ids}

    for inst_idx, inst_id in enumerate(inst_ids):
      n_subj = counts[inst_idx]
      if n_subj <= 0:
        continue
      for j in range(n_subj):
        name = make_subject_name(inst_idx, j)
        subj = api.create_subject_for_institution(inst_id, name=name)
        subjects_by_inst[inst_id].append(subj)
      inst_country = inst_by_id[inst_id]["country"]
      print(f"  - institution[{inst_idx}] {inst_id} country={inst_country}: {n_subj} materias")

    total_subjects = sum(len(v) for v in subjects_by_inst.values())
    print(f"  - total materias creadas: {total_subjects}")

    print("\n5) Cargar exams (system según institution.country)")
    today = date.today()

    base_per_student = max(1, n_exams_total // len(students))
    remainder = n_exams_total - base_per_student * len(students)

    exams_created = 0
    for idx, s in enumerate(students):
      sid = str(s.get("_id") or s.get("id"))
      student_periods = student_inst_map[sid]

      per = jitter_amount(base_per_student, "exams", min_value=1)
      if remainder > 0:
        per += 1
        remainder -= 1

      pool: List[Tuple[str, Dict[str, Any], date, Optional[date]]] = []
      for inst_id, start_d, end_d in student_periods:
        subj_list = subjects_by_inst.get(inst_id, [])
        if not subj_list:
          continue
        take = min(len(subj_list), random.randint(5, 20))
        for subj in random.sample(subj_list, k=take):
          pool.append((inst_id, subj, start_d, end_d))

      if not pool:
        print(f"  - WARN student {sid}: sin materias en sus instituciones, no se cargan exams")
        continue

      for _ in range(per):
        inst_id, subj, start_d, end_d = rchoice(pool)
        end_effective = end_d or today
        exam_date = rand_date_between(start_d, end_effective)

        inst_country = inst_by_id[inst_id]["country"]  # ISO-3
        system = rchoice(SYSTEMS_BY_COUNTRY[inst_country])

        if system not in valueExams:
            raise ValueError(f"No value mapping definido para system {system}")

        value = random.choice(valueExams[system])

        payload = {
          "subjectId": subj["id"],            # UUID (neo4j)
          "studentId": sid,                   # ObjectId hex (mongo)
          "institutionId": inst_id,           # ObjectId hex (mongo)
          "name": f"{rchoice(EXAM_TYPES)} - {subj['name']}",
          "system": system,
          "type": rchoice(EXAM_TYPES),
          "country": inst_country,            # ISO-3
          "grade": rchoice(GRADE_LABELS),
          "date": exam_date.isoformat(),
          "value": value,
        }
        api.create_exam(payload)
        exams_created += 1

        # opcional: arista Took en Neo4j
        if random.random() < 0.35:
          api.link_student_subject(
            student_id=sid,
            subject_id=subj["id"],
            start=start_d.isoformat(),
            grade=value,
            end=iso(end_d),
          )

      print(f"  - student[{idx}] {sid}: exams creados ~{per}")

    print("\n✅ Seed finalizado")
    print(f"- alumnos creados:        {len(students)}")
    print(f"- instituciones creadas:  {len(inst_ids)}")
    print(f"- materias creadas:       {total_subjects}")
    print(f"- exams creados:          {exams_created}")

  finally:
    api.close()


if __name__ == "__main__":
  main()