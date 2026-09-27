"""Prepare a runnable dataset from reference and synthetic inputs."""
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
from .loader import load_data

def prepare_dataset(repo):
    repo = Path(repo).resolve()
    sources = {
        "curricula.csv": repo/"data/raw/curricula.csv",
        "curriculum_courses.csv": repo/"data/raw/curriculum_courses.csv",
        "student.csv": repo/"data/synthetic/student.csv",
        "student_course_status.csv": repo/"data/synthetic/student_course_status.csv",
        "student_study_plan.csv": repo/"data/synthetic/student_study_plan.csv",
    }
    with TemporaryDirectory() as temp:
        staging = Path(temp)
        for name, source in sources.items():
            shutil.copyfile(source, staging/name)
        tables, warnings = load_data(staging)
        destination = repo/"data/processed"
        destination.mkdir(parents=True, exist_ok=True)
        for name in sources:
            shutil.copyfile(staging/name, destination/name)
    return destination, warnings
