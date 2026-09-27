"""Feature extraction only; no inferred ML training labels."""
from collections import defaultdict

def student_features(tables):
    failures = defaultdict(set)
    for row in tables["student_course_status"]:
        if row["status"] == "FAILED":
            failures[(row["student_id"],row["academic_term"])].add(row["course_id"])
    return [{"student_id": s["student_id"], "academic_term": s["academic_term"],
             "accumulated_credits": float(s["accumulated_credits"]),
             "failed_course_count": len(failures[(s["student_id"],s["academic_term"])]),
             "current_semester": int(s["current_semester"])} for s in tables["students"]]
