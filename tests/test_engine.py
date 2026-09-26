import copy
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
import shutil

from ojt_risk.engine import DataError, allocate_classes, analyze, load_data

SAMPLE = Path(__file__).resolve().parent / "fixtures" / "demo"


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tables, _ = load_data(SAMPLE)

    def run_report(self):
        return analyze(self.tables, "2026_HK1", "2026_HK2")

    def test_sample_forecast_and_missing_plan(self):
        report = self.run_report()
        first = report["forecasts"][0]
        self.assertEqual(first["projected_credits"], 73)
        self.assertEqual(first["projected_failed_course_count"], 2)
        self.assertTrue(first["projected_ojt_eligible"])
        self.assertIsNone(report["forecasts"][2]["projected_ojt_eligible"])

    def test_eligibility_boundaries(self):
        for credits in (69, 70, 71):
            for failed_count in (1, 2, 3):
                with self.subTest(credits=credits, failed=failed_count):
                    self.tables, _ = load_data(SAMPLE)
                    self.tables["students"][0]["accumulated_credits"] = Decimal(credits)
                    statuses = self.tables["student_course_status"][:3]
                    for i, status in enumerate(statuses):
                        status["status"] = "FAILED" if i < failed_count else "PASSED"
                    self.tables["student_study_plan"] = []
                    self.assertEqual(self.run_report()["evaluations"][0]["ojt_eligible"],
                                     credits >= 70 and failed_count <= 2)

    def test_credits_alone_do_not_qualify_forecast(self):
        self.tables["student_study_plan"] = self.tables["student_study_plan"][:1]
        forecast = self.run_report()["forecasts"][0]
        self.assertEqual(forecast["projected_credits"], 70)
        self.assertFalse(forecast["projected_ojt_eligible"])

    def test_class_allocation_conserves_students(self):
        for count in range(250):
            sizes, waiting = allocate_classes(count)
            self.assertEqual(sum(sizes) + waiting, count)
            self.assertTrue(all(18 <= size <= 22 for size in sizes))
        self.assertEqual(allocate_classes(17), ([], 17))
        self.assertEqual(allocate_classes(40), ([20, 20], 0))
        self.assertEqual(allocate_classes(23), ([22], 1))

    def test_double_counted_credit_rejected(self):
        self.tables["student_study_plan"][-1]["credits_to_gain"] = Decimal(3)
        with self.assertRaises(DataError):
            self.run_report()

    def test_missing_status_rejected(self):
        self.tables["student_course_status"] = []
        with self.assertRaises(DataError):
            self.run_report()

    def test_import_extra_columns_and_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "sample"
            shutil.copytree(SAMPLE, target)
            path = target / "students.csv"
            rows = path.read_text(encoding="utf-8").splitlines()
            path.write_text("\n".join([rows[0] + ",new_column"] + [r + ",extra" for r in rows[1:]]) + "\n", encoding="utf-8")
            _, warnings = load_data(target)
            self.assertTrue(any("new_column" in w for w in warnings))
            with path.open("a", encoding="utf-8") as stream:
                stream.write(rows[1] + ",extra\n")
            with self.assertRaises(DataError):
                load_data(target)

    def test_repeat_analysis_is_deterministic(self):
        before = copy.deepcopy(self.tables)
        self.assertEqual(self.run_report(), self.run_report())
        self.assertEqual(before, self.tables)


if __name__ == "__main__":
    unittest.main()
