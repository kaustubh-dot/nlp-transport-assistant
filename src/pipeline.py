"""End-to-End NLU Transport Assistant pipeline orchestrator.

Coordinates query flow:
Raw Query -> Text Normalization -> Intent Classification & Slot Extraction
          -> SQLite Transit Retrieval -> Deterministic Hindi Response
"""

from typing import Dict, Any, Optional
from src.normalization import normalize_text
from src.entity_extractor import EntityExtractor
from src.intent_classifier import get_classifier, BaseIntentClassifier
from src.retrieval import TransitRetriever
from src.response_generator import ResponseGenerator


class TransportAssistant:
    """Full multimodal transport assistant pipeline."""

    def __init__(
        self,
        model_type: str = "baseline",
        db_path: Optional[str] = None
    ):
        self.classifier: BaseIntentClassifier = get_classifier(model_type)
        self.extractor = EntityExtractor()
        self.retriever = TransitRetriever(db_path=db_path)
        self.generator = ResponseGenerator()

    def process_query(self, query: str) -> Dict[str, Any]:
        """Processes a natural language query end-to-end.

        Args:
            query: Input question in Hindi or Hinglish.

        Returns:
            Dictionary containing intent, confidence, slots, db_result, and response_hi.
        """
        # 1. Normalization
        norm_query = normalize_text(query)

        # 2. Intent Classification
        intent, confidence = self.classifier.predict_with_confidence(norm_query)

        # 3. Entity & Slot Extraction
        slots = self.extractor.extract(query)

        # 4. Structured Transport Retrieval
        db_result = self._retrieve_data(intent, slots)

        # 5. Deterministic Response Generation
        response_hi = self.generator.generate(
            intent=intent,
            slots=slots,
            retrieval_data=db_result,
            confidence=confidence
        )

        # The bundled records are fixtures, not an independently verified feed.
        if intent in {"route_query", "service_availability", "accessibility", "station_information"}:
            response_hi = "डेमो: परिवहन डेटा सत्यापित नहीं है। " + response_hi

        return {
            "data_status": "unverified_demo",
            "model_backend": "heuristic" if self.classifier.model is None else type(self.classifier).__name__,
            "raw_query": query,
            "normalized_query": norm_query,
            "intent": intent,
            "confidence": confidence,
            "slots": slots,
            "db_result": db_result,
            "response_hi": response_hi
        }

    def _retrieve_data(self, intent: str, slots: Dict[str, Any]) -> Dict[str, Any]:
        """Queries SQLite database according to intent and extracted slots."""
        origin = slots.get("origin")
        destination = slots.get("destination")
        station = slots.get("station") or origin or destination
        mode = slots.get("transport_mode")

        result: Dict[str, Any] = {}

        if intent == "route_query" and origin and destination:
            routes = self.retriever.get_route(origin, destination, mode)
            result["routes"] = routes
            if origin:
                info = self.retriever.get_station_info(origin)
                if info:
                    result["origin_name_hi"] = info.get("name_hi")
            if destination:
                info = self.retriever.get_station_info(destination)
                if info:
                    result["dest_name_hi"] = info.get("name_hi")

        elif intent == "service_availability" and origin and destination:
            avail = self.retriever.check_availability(origin, destination, mode)
            result.update(avail)

        elif intent == "service_timing":
            timings = self.retriever.get_service_timing(mode or "metro")
            result["timings"] = timings

        elif intent == "accessibility" and station:
            fac = self.retriever.get_accessibility_info(station)
            result["facilities"] = fac

        elif intent == "ticketing":
            ticketing = self.retriever.get_ticketing_info(origin, destination, mode or "metro")
            result.update(ticketing)

        elif intent == "station_information" and station:
            st_info = self.retriever.get_station_info(station)
            result["station_info"] = st_info

        return result
