import csv
import shutil
import tempfile
import unittest
from pathlib import Path
from ojt_ai.data.preprocessing import prepare_dataset
from ojt_ai.data.loader import load_data

DEMO=Path(__file__).resolve().parents[2]/"data/synthetic/demo"
class PreprocessingTests(unittest.TestCase):
    def test_prepare_supports_student_filename_and_semester_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for folder in ("raw","synthetic"):
                (root/"data"/folder).mkdir(parents=True)
            for name in ("curricula.csv","curriculum_courses.csv"):
                shutil.copyfile(DEMO/name,root/"data/raw"/name)
            for name in ("student_course_status.csv","student_study_plan.csv"):
                shutil.copyfile(DEMO/name,root/"data/synthetic"/name)
            shutil.copyfile(DEMO/"students.csv",root/"data/synthetic/student.csv")
            path=root/"data/raw/curriculum_courses.csv"
            with path.open("a",encoding="utf-8") as f:
                f.write("IS-K18D,INTRO,Orientation,0,0\n")
            output,_=prepare_dataset(root)
            tables,_=load_data(output)
            self.assertEqual(len(tables["students"]),3)
            self.assertEqual(tables["curriculum_courses"][-1]["recommended_semester"],0)
