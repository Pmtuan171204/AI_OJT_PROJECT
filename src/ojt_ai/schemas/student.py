from dataclasses import dataclass

@dataclass(frozen=True)
class StudentFeatures:
    student_id: str
    accumulated_credits: float
    failed_course_count: int
    current_semester: int
