"""
SupportIQ — Runtime Intent Classifier
Loads the trained pipeline once at module import and exposes a clean
predict() API used by the FastAPI chat service.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Optional

import joblib
import numpy as np

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from preprocessor import preprocess

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ML_DIR = pathlib.Path(__file__).resolve().parent
_MODELS_DIR = _ML_DIR / "models"
_ACTIVE_PIPELINE_PATH = _MODELS_DIR / "active_pipeline.pkl"
_METADATA_PATH = _MODELS_DIR / "intent_metadata.json"
_CLASSES_PATH = _MODELS_DIR / "label_classes.json"

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class IntentResult:
    """Structured result returned by the classifier for a single query."""

    # Primary prediction
    intent: str
    confidence: float                  # probability of the top intent [0, 1]
    category: str
    response_template: str
    requires_escalation: bool
    priority_level: str                # low | medium | high

    # Runner-up alternatives (top-3 excluding winner)
    alternatives: list[dict] = field(default_factory=list)

    # Flags set by post-processing
    is_fallback: bool = False          # True when confidence < threshold
    escalate: bool = False             # True when requires_escalation OR complaint

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "confidence": round(self.confidence, 4),
            "category": self.category,
            "response_template": self.response_template,
            "requires_escalation": self.requires_escalation,
            "priority_level": self.priority_level,
            "alternatives": self.alternatives,
            "is_fallback": self.is_fallback,
            "escalate": self.escalate,
        }


# ---------------------------------------------------------------------------
# Classifier (singleton)
# ---------------------------------------------------------------------------


class IntentClassifier:
    """
    Wraps the trained sklearn Pipeline.  Loaded once; safe to reuse across
    FastAPI requests (stateless after __init__).
    """

    # Confidence below this → fallback_unclear
    # For a 22-class problem with ~20 samples/intent, calibrated SVM
    # probabilities are lower than in binary problems; 0.35 is appropriate.
    CONFIDENCE_THRESHOLD: float = 0.35

    def __init__(self) -> None:
        self._pipeline = None
        self._metadata: dict[str, dict] = {}
        self._classes: list[str] = []
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load model artefacts from disk.  Called once at startup."""
        if not _ACTIVE_PIPELINE_PATH.exists():
            raise FileNotFoundError(
                f"Trained model not found at {_ACTIVE_PIPELINE_PATH}. "
                "Run `python scripts/train_models.py` first."
            )

        self._pipeline = joblib.load(_ACTIVE_PIPELINE_PATH)

        if _METADATA_PATH.exists():
            with open(_METADATA_PATH, encoding="utf-8") as f:
                self._metadata = json.load(f)

        if _CLASSES_PATH.exists():
            with open(_CLASSES_PATH, encoding="utf-8") as f:
                self._classes = json.load(f)

        self._loaded = True

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, text: str) -> IntentResult:
        """
        Classify a single user utterance.

        Steps:
          1. Preprocess raw text
          2. Get probability distribution from the pipeline
          3. Top-1 intent + confidence
          4. Apply confidence threshold → fallback if below it
          5. Escalation flag from metadata OR from complaint intent
          6. Return IntentResult

        Parameters
        ----------
        text : str
            Raw user message (not pre-processed).

        Returns
        -------
        IntentResult
        """
        if not self._loaded:
            self.load()

        # Preprocess
        processed = preprocess(text)

        # Predict probabilities
        proba = self._pipeline.predict_proba([processed])[0]
        classes = self._pipeline.classes_

        # Sort by probability descending
        ranked_idx = np.argsort(proba)[::-1]
        top_intent = classes[ranked_idx[0]]
        top_confidence = float(proba[ranked_idx[0]])

        # Alternatives (top 3 after the winner)
        alternatives = [
            {"intent": classes[i], "confidence": round(float(proba[i]), 4)}
            for i in ranked_idx[1:4]
        ]

        # Apply confidence threshold
        is_fallback = top_confidence < self.CONFIDENCE_THRESHOLD
        if is_fallback:
            top_intent = "fallback_unclear"
            top_confidence = float(proba[ranked_idx[0]])  # keep raw score for logging

        # Retrieve metadata
        meta = self._metadata.get(top_intent, {})
        category = meta.get("category", "Unknown")
        response_template = meta.get(
            "response_template",
            "I'm not sure I understood that. Could you please rephrase?"
        )
        requires_escalation = meta.get("requires_escalation", False)
        priority_level = meta.get("priority_level", "low")

        # Escalation: explicit metadata OR explicit escalation intent
        escalate = requires_escalation or top_intent == "escalation_request"

        return IntentResult(
            intent=top_intent,
            confidence=top_confidence,
            category=category,
            response_template=response_template,
            requires_escalation=requires_escalation,
            priority_level=priority_level,
            alternatives=alternatives,
            is_fallback=is_fallback,
            escalate=escalate,
        )

    def predict_batch(self, texts: list[str]) -> list[IntentResult]:
        """Classify a list of utterances. Useful for batch analytics."""
        return [self.predict(t) for t in texts]

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    def get_intent_names(self) -> list[str]:
        return list(self._classes)

    def get_metadata(self, intent_name: str) -> Optional[dict]:
        return self._metadata.get(intent_name)


# ---------------------------------------------------------------------------
# Module-level singleton — import and use directly in services
# ---------------------------------------------------------------------------

classifier = IntentClassifier()


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Loading model …")
    classifier.load()
    print(f"Model loaded. {len(classifier.get_intent_names())} intents.\n")

    test_queries = [
        "I can't log into my account",
        "Please refund my money",
        "Where is my order?",
        "The app keeps crashing on my phone",
        "I want to talk to a real person",
        "Cancel my subscription please",
        "Hello",
        "xyzzy random nonsense",
    ]

    print(f"{'Query':<50} {'Intent':<35} {'Conf':>6}  {'Fallback'}")
    print("-" * 110)
    for q in test_queries:
        r = classifier.predict(q)
        print(f"{q:<50} {r.intent:<35} {r.confidence:>6.3f}  {'YES' if r.is_fallback else 'no'}")
