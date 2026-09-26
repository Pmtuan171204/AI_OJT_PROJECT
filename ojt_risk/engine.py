"""CSV validation and deterministic business rules. No external services."""

import csv
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path


@dataclass(frozen=True)
class Rules:
    min_credits: int = 70
    max_failed: int = 2
    class_min: int = 18
    class_target: int = 20
    class_max: int = 22


SCHEMA = {
    "students": "student_id full_name email cohort curriculum_code current_semester academic_term accumulated_credits",
    "curricula": "curriculum_code",
    "curriculum_courses": "curriculum_code course_id course_name credits recommended_semester",
    "student_course_status": "student_id academic_term course_id status",
    "student_study_plan": "student_id academic_term semester_number course_id credits_to_gain plan_source",
}
KEYS = {
    "students": ("student_id", "academic_term"),
    "curricula": ("curriculum_code",),
    "curriculum_courses": ("curriculum_code", "course_id"),
    "student_course_status": ("student_id", "academic_term", "course_id"),
    "student_study_plan": ("student_id", "academic_term", "course_id"),
}
NUMBERS = {
    "students": ("current_semester", "accumulated_credits"),
    "curriculum_courses": ("credits", "recommended_semester"),
    "student_study_plan": ("semester_number", "credits_to_gain"),
}


class DataError(ValueError):
    pass


def load_data(directory):
    """Reject invalid batches; tolerate extra columns. Headers required for empty tables."""
    tables, warnings = {}, []
    for table, fields in SCHEMA.items():
        path = Path(directory) / f"{table}.csv"
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            headers = reader.fieldnames or []
            if len(headers) != len(set(headers)):
                raise DataError(f"{path.name}: duplicate headers")
            missing = set(fields.split()) - set(headers)
            if missing:
                raise DataError(f"{path.name}: missing columns {sorted(missing)}")
            extra = set(headers) - set(fields.split())
            if extra:
                warnings.append(f"{path.name}: unused columns {sorted(extra)}")
            rows, seen = [], set()
            for line, raw in enumerate(reader, 2):
                context = f"{path.name}:{line}"
                if None in raw:
                    raise DataError(f"{context}: too many CSV fields")
                row = {key: (raw.get(key) or "").strip() for key in fields.split()}
                for key, value in row.items():
                    if not value and key != "email":
                        raise DataError(f"{context}: empty {key}")
                for key in NUMBERS.get(table, ()):
                    try:
                        value = Decimal(row[key])
                    except InvalidOperation as exc:
                        raise DataError(f"{context}: invalid number {key}") from exc
                    if not value.is_finite() or value < 0:
                        raise DataError(f"{context}: invalid nonnegative number {key}")
                    if key in ("current_semester", "recommended_semester", "semester_number"):
                        if value < 1 or value != int(value):
                            raise DataError(f"{context}: {key} must be a positive integer")
                    row[key] = value
                identity = tuple(row[key] for key in KEYS[table])
                if identity in seen:
                    raise DataError(f"{context}: duplicate key {identity}")
                seen.add(identity)
                rows.append(row)
            tables[table] = rows
    validate_relations(tables)
    return tables, warnings


def validate_relations(tables):
    curricula = {r["curriculum_code"] for r in tables["curricula"]}
    courses = {(r["curriculum_code"], r["course_id"]): r for r in tables["curriculum_courses"]}
    students = {(r["student_id"], r["academic_term"]): r for r in tables["students"]}
    by_id = defaultdict(list)
    for row in students.values():
        if row["curriculum_code"] not in curricula:
            raise DataError(f"Unknown curriculum for {row['student_id']}")
        by_id[row["student_id"]].append(row)
    for row in courses.values():
        if row["curriculum_code"] not in curricula:
            raise DataError(f"Unknown curriculum {row['curriculum_code']}")
    for row in tables["student_course_status"]:
        student = students.get((row["student_id"], row["academic_term"]))
        if not student or (student["curriculum_code"], row["course_id"]) not in courses:
            raise DataError(f"Invalid status reference: {row}")
        if row["status"] not in {"PASSED", "FAILED", "IN_PROGRESS", "NOT_TAKEN"}:
            raise DataError(f"Invalid status: {row['status']}")
    for row in tables["student_study_plan"]:
        candidates = by_id[row["student_id"]]
        matches = [courses[(s["curriculum_code"], row["course_id"])] for s in candidates
                   if (s["curriculum_code"], row["course_id"]) in courses]
        if not matches or row["credits_to_gain"] > max(c["credits"] for c in matches):
            raise DataError(f"Invalid study plan reference or credits: {row}")
        if row["plan_source"] not in {"REGISTERED", "CURRICULUM_ASSUMPTION"}:
            raise DataError(f"Invalid plan source: {row['plan_source']}")


def allocate_classes(count, rules=Rules()):
    """Maximize placed students, then prefer sizes close to target."""
    candidates = []
    for classes in range(1, count // rules.class_min + 1):
        placed = min(count, classes * rules.class_max)
        base, extra = divmod(placed, classes)
        sizes = [base + 1] * extra + [base] * (classes - extra)
        deviation = sum(abs(size - rules.class_target) for size in sizes)
        candidates.append((count - placed, deviation, classes, sizes))
    if not candidates:
        return [], count
    waiting, _, _, sizes = min(candidates)
    return sizes, waiting


def analyze(tables, evaluation_term, target_term, rules=Rules()):
    if evaluation_term == target_term:
        raise DataError("Evaluation term and target term must differ")
    students = [s for s in tables["students"] if s["academic_term"] == evaluation_term]
    if not students:
        raise DataError(f"No students in evaluation term {evaluation_term}")
    courses = {(r["curriculum_code"], r["course_id"]): r for r in tables["curriculum_courses"]}
    results, forecasts, groups = [], [], defaultdict(set)
    for student in students:
        sid, curriculum = student["student_id"], student["curriculum_code"]
        statuses = {r["course_id"]: r["status"] for r in tables["student_course_status"]
                    if r["student_id"] == sid and r["academic_term"] == evaluation_term}
        # At least one status is required; actual completeness is an import contract.
        if not statuses:
            raise DataError(f"Missing course status data for {sid}")
        failed = {code for code, status in statuses.items() if status == "FAILED"}
        credits = student["accumulated_credits"]
        reasons = []
        if credits < rules.min_credits:
            reasons.append("INSUFFICIENT_CREDITS")
        if len(failed) > rules.max_failed:
            reasons.append("TOO_MANY_FAILED_COURSES")
        results.append({"student_id": sid, "academic_term": evaluation_term,
                        "accumulated_credits": float(credits), "total_courses_failed": len(failed),
                        "failed_course_ids": sorted(failed),
                        "failed_course_credits": float(sum(courses[(curriculum, c)]["credits"] for c in failed)),
                        "credits_missing_for_ojt": float(max(0, rules.min_credits - credits)),
                        "ojt_eligible": not reasons, "ineligibility_reasons": reasons})
        if reasons:
            for course in failed:
                groups[course].add(sid)
        if student["current_semester"] != 4:
            continue
        plan = [p for p in tables["student_study_plan"] if p["student_id"] == sid
                and p["academic_term"] == target_term and p["semester_number"] == 5]
        forecast = {"student_id": sid, "evaluation_term": evaluation_term, "target_term": target_term}
        if not plan:
            forecasts.append({**forecast, "forecast_status": "INSUFFICIENT_DATA",
                              "projected_ojt_eligible": None})
            continue
        for p in plan:
            course = courses.get((curriculum, p["course_id"]))
            if not course or p["credits_to_gain"] > course["credits"]:
                raise DataError(f"Plan does not match current curriculum for {sid}")
            if statuses.get(p["course_id"]) == "PASSED" and p["credits_to_gain"] != 0:
                raise DataError(f"Double-counted credits for {sid}/{p['course_id']}")
        gain = sum(p["credits_to_gain"] for p in plan)
        remaining = failed - {p["course_id"] for p in plan}
        forecasts.append({**forecast, "forecast_status": "AVAILABLE",
                          "forecast_basis": sorted({p["plan_source"] for p in plan}),
                          "assumption": "Pass all courses in the supplied semester 5 plan",
                          "expected_next_credits": float(gain), "projected_credits": float(credits + gain),
                          "projected_failed_course_ids": sorted(remaining),
                          "projected_failed_course_count": len(remaining),
                          "projected_missing_credits": float(max(0, rules.min_credits - credits - gain)),
                          "projected_ojt_eligible": credits + gain >= rules.min_credits and len(remaining) <= rules.max_failed})
    recommendations = []
    for course, ids in sorted(groups.items()):
        sizes, waiting = allocate_classes(len(ids), rules)
        recommendations.append({"academic_term": evaluation_term, "course_id": course,
                                "student_ids": sorted(ids), "student_count": len(ids),
                                "suggested_class_count": len(sizes), "suggested_class_sizes": sizes,
                                "waiting_student_count": waiting,
                                "recommendation_status": "PROPOSED" if sizes else "MONITORING"})
    return {"evaluations": results, "recommendations": recommendations, "forecasts": forecasts}
