"""Fixed intent adapter for deterministic production regression tests."""
from src.nlp_v2.contracts import IntentPrediction


class FixedClassifier:
    def __init__(self,label):self.label=label
    def predict(self,query):return IntentPrediction(self.label,(self.label,),1.0)
