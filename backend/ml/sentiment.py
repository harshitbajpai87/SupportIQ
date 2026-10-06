"""
SupportIQ — Sentiment Analyser
Uses NLTK VADER (Valence Aware Dictionary and sEntiment Reasoner),
a rule-based model tuned for short, informal social-media-style text —
exactly the kind of language used in customer support messages.

No training required. Returns a structured SentimentResult with:
  - label   : positive | neutral | negative
  - compound: float in [-1, 1]  (overall score)
  - scores  : { neg, neu, pos } raw VADER proportions
  - intensity: mild | moderate | strong
"""

from __future__ import annotations

from dataclasses import dataclass

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from preprocessor import ensure_nltk_data, clean

# Ensure VADER lexicon is present
def _ensure_vader() -> None:
    try:
        nltk.data.find("sentiment/vader_lexicon.zip")
    except LookupError:
        nltk.download("vader_lexicon", quiet=True)

ensure_nltk_data()
_ensure_vader()

# ---------------------------------------------------------------------------
# Thresholds  (VADER standard recommendations)
# ---------------------------------------------------------------------------

_POSITIVE_THRESHOLD = 0.05
_NEGATIVE_THRESHOLD = -0.05

# Intensity bands based on |compound|
_MILD_MAX = 0.35
_MODERATE_MAX = 0.65
# above 0.65 → strong


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


@dataclass
class SentimentResult:
    label: str          # positive | neutral | negative
    compound: float     # [-1, 1]
    neg: float          # proportion negative
    neu: float          # proportion neutral
    pos: float          # proportion positive
    intensity: str      # mild | moderate | strong

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "compound": round(self.compound, 4),
            "neg": round(self.neg, 4),
            "neu": round(self.neu, 4),
            "pos": round(self.pos, 4),
            "intensity": self.intensity,
        }

    @property
    def is_negative(self) -> bool:
        return self.label == "negative"

    @property
    def is_positive(self) -> bool:
        return self.label == "positive"


# ---------------------------------------------------------------------------
# Analyser singleton
# ---------------------------------------------------------------------------

_analyser: SentimentIntensityAnalyzer | None = None


def _get_analyser() -> SentimentIntensityAnalyzer:
    global _analyser
    if _analyser is None:
        _analyser = SentimentIntensityAnalyzer()
    return _analyser


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyse(text: str) -> SentimentResult:
    """
    Analyse the sentiment of a single user message.

    VADER is applied to the lightly cleaned text (contractions expanded,
    unicode normalised) rather than the fully stemmed version so that
    capitalisation, punctuation, and exclamation marks — which VADER uses
    as sentiment intensifiers — are preserved.

    Parameters
    ----------
    text : str
        Raw user message.

    Returns
    -------
    SentimentResult
    """
    # Light clean only — preserve casing / punctuation for VADER
    cleaned = clean(text)

    sia = _get_analyser()
    scores = sia.polarity_scores(cleaned)

    compound = scores["compound"]

    if compound >= _POSITIVE_THRESHOLD:
        label = "positive"
    elif compound <= _NEGATIVE_THRESHOLD:
        label = "negative"
    else:
        label = "neutral"

    abs_compound = abs(compound)
    if abs_compound <= _MILD_MAX:
        intensity = "mild"
    elif abs_compound <= _MODERATE_MAX:
        intensity = "moderate"
    else:
        intensity = "strong"

    return SentimentResult(
        label=label,
        compound=compound,
        neg=scores["neg"],
        neu=scores["neu"],
        pos=scores["pos"],
        intensity=intensity,
    )


def analyse_batch(texts: list[str]) -> list[SentimentResult]:
    """Analyse a list of messages. Used by the analytics service."""
    return [analyse(t) for t in texts]


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    samples = [
        ("I'm really happy with your service, thank you!", "expect: positive"),
        ("My payment was declined and I'm very frustrated!!!", "expect: negative"),
        ("Where is my order", "expect: neutral"),
        ("This is absolutely terrible, worst service ever", "expect: negative/strong"),
        ("Thanks a lot, that worked perfectly!", "expect: positive"),
        ("I want to cancel my subscription", "expect: neutral/negative"),
        ("You've been a great help, brilliant!", "expect: positive"),
        ("This is unacceptable I've been waiting for days", "expect: negative"),
    ]

    print(f"{'Text':<55} {'Label':<10} {'Compound':>9}  {'Intensity'}")
    print("-" * 95)
    for text, note in samples:
        r = analyse(text)
        print(f"{text:<55} {r.label:<10} {r.compound:>9.4f}  {r.intensity}   # {note}")
