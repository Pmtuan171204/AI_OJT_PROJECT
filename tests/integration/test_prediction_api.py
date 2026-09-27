import unittest
from pathlib import Path
try:
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_data_directory
except ImportError:
    TestClient = None

@unittest.skipIf(TestClient is None, "Install API/dev extras to run HTTP integration tests")
class PredictionApiTests(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[get_data_directory] = lambda: Path(__file__).resolve().parents[1]/"fixtures/demo"
        self.client=TestClient(app)
    def tearDown(self):
        app.dependency_overrides.clear()
    def test_health(self):
        response=self.client.get("/health")
        self.assertEqual(response.status_code,200)
        self.assertFalse(response.json()["ml_model_ready"])
    def test_prediction(self):
        response=self.client.post("/prediction",json={"evaluation_term":"2026_HK1","target_term":"2026_HK2"})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()["mode"],"rules")
        self.assertEqual(len(response.json()["evaluations"]),3)
    def test_invalid_terms(self):
        response=self.client.post("/prediction",json={"evaluation_term":"2026_HK1","target_term":"2026_HK1"})
        self.assertEqual(response.status_code,422)
