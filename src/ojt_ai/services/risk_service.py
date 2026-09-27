"""Eligibility, class suggestions and conditional forecasts, not ML predictions."""
from collections import defaultdict
from ojt_ai.data.validator import DataError
from ojt_ai.rules.eligibility import Rules, allocate_classes

def analyze(tables, evaluation_term, target_term, rules=Rules()):
    if evaluation_term == target_term:
        raise DataError("Evaluation term and target term must differ")
    students = [s for s in tables["students"] if s["academic_term"] == evaluation_term]
    if not students:
        raise DataError(f"No students in evaluation term {evaluation_term}")
    courses = {(r["curriculum_code"], r["course_id"]): r for r in tables["curriculum_courses"]}
    status_index = defaultdict(dict)
    for row in tables["student_course_status"]:
        status_index[(row["student_id"], row["academic_term"])][row["course_id"]] = row["status"]
    results, forecasts, groups = [], [], defaultdict(set)
    for student in students:
        sid, curriculum = student["student_id"], student["curriculum_code"]
        statuses = status_index[(sid, evaluation_term)]
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
