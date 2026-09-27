"""Input schemas and relational integrity checks."""
from collections import defaultdict

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


