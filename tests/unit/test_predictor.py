import unittest
from ojt_ai.ml.predictor import Predictor, ModelNotReadyError

class PredictorTests(unittest.TestCase):
    def test_untrained_model_does_not_invent_prediction(self):
        with self.assertRaises(ModelNotReadyError):
            Predictor().predict([])
