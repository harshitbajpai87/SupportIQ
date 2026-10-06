"""
SupportIQ — Entity Extractor
Extracts structured entities from user messages using regex patterns
and NLTK Named Entity Recognition.

Entities extracted:
  - order_id        — numeric IDs like #12345 or "order 98765"
  - ticket_id       — ticket references like TKT-1234
  - email           — email addresses
  - phone           — phone numbers
  - date            — date expressions
  - amount          — currency amounts
  - product_name    — NLTK NER ORGANIZATION / PRODUCT nouns (heuristic)
  - person_name     — NLTK NER PERSON
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import nltk
from nltk import ne_chunk, pos_tag, word_tokenize
from nltk.tree import Tree

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from preprocessor import ensure_nltk_data

ensure_nltk_data()

# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


@dataclass
class Entities:
    order_ids: list[str] = field(default_factory=list)
    ticket_ids: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    amounts: list[str] = field(default_factory=list)
    person_names: list[str] = field(default_factory=list)
    organisations: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not any([
            self.order_ids, self.ticket_ids, self.emails, self.phones,
            self.dates, self.amounts, self.person_names, self.organisations,
        ])

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_ids": self.order_ids,
            "ticket_ids": self.ticket_ids,
            "emails": self.emails,
            "phones": self.phones,
            "dates": self.dates,
            "amounts": self.amounts,
            "person_names": self.person_names,
            "organisations": self.organisations,
        }


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_PATTERNS: dict[str, re.Pattern] = {
    # Order IDs: #12345 | order 12345 | order no. 12345 | ORD-12345
    "order_id": re.compile(
        r"(?:order\s*(?:no\.?|number|#|id)?\s*[:\-]?\s*|#|ORD-?)(\d{4,10})",
        re.IGNORECASE,
    ),
    # Ticket IDs: TKT-1234 | TICKET-1234 | ticket #1234
    "ticket_id": re.compile(
        r"(?:TKT|TICKET|ticket\s*#?)\s*[-]?\s*(\d{4,8})",
        re.IGNORECASE,
    ),
    # Email
    "email": re.compile(
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
    ),
    # Phone: international and domestic formats
    "phone": re.compile(
        r"(?:\+?\d{1,3}[\s\-]?)?(?:\(?\d{2,4}\)?[\s\-]?)?\d{3,4}[\s\-]?\d{4}"
    ),
    # Currency amounts: must have a currency prefix OR suffix to avoid false matches
    # Matches: $100, ₹500, Rs. 1000, 49.99 USD, 200 INR
    "amount": re.compile(
        r"(?:(?:Rs\.?\s*|₹|INR\s*|\$|€|£|USD\s*|EUR\s*)\d{1,6}(?:[.,]\d{1,2})?|"
        r"\d{1,6}(?:[.,]\d{1,2})?\s*(?:USD|INR|EUR|GBP))",
        re.IGNORECASE,
    ),
    # Dates: common formats
    "date": re.compile(
        r"\b(?:\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|"          # dd/mm/yyyy
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        r"[\w]*\.?\s+\d{1,2},?\s+\d{4}|"                      # Month DD, YYYY
        r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\w]*\s+\d{4}|"
        r"(?:yesterday|today|tomorrow|last\s+\w+|next\s+\w+|"
        r"last\s+month|this\s+month|last\s+week))\b",
        re.IGNORECASE,
    ),
}


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------


def _extract_regex(text: str) -> dict[str, list[str]]:
    """Run all regex patterns against the raw text."""
    results: dict[str, list[str]] = {}
    for entity_type, pattern in _PATTERNS.items():
        matches = pattern.findall(text)
        # findall returns groups if present; flatten
        cleaned = [m.strip() for m in matches if m.strip()]
        if cleaned:
            results[entity_type] = list(dict.fromkeys(cleaned))  # deduplicate, preserve order
    return results


def _extract_ner(text: str) -> tuple[list[str], list[str]]:
    """
    Use NLTK chunked NER to extract PERSON and ORGANIZATION entities.
    Returns (person_names, organisations).
    """
    persons: list[str] = []
    orgs: list[str] = []

    try:
        tokens = word_tokenize(text)
        tagged = pos_tag(tokens)
        chunked = ne_chunk(tagged, binary=False)

        for subtree in chunked:
            if isinstance(subtree, Tree):
                entity_text = " ".join(word for word, tag in subtree.leaves())
                label = subtree.label()
                if label == "PERSON":
                    persons.append(entity_text)
                elif label in ("ORGANIZATION", "GPE"):
                    orgs.append(entity_text)
    except Exception:
        # NER is best-effort; never crash the chat service
        pass

    return persons, orgs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_entities(text: str) -> Entities:
    """
    Extract all entities from a raw user message.

    Parameters
    ----------
    text : str
        Raw (un-preprocessed) user message.

    Returns
    -------
    Entities dataclass
    """
    regex_results = _extract_regex(text)
    persons, orgs = _extract_ner(text)

    return Entities(
        order_ids=regex_results.get("order_id", []),
        ticket_ids=regex_results.get("ticket_id", []),
        emails=regex_results.get("email", []),
        phones=regex_results.get("phone", []),
        dates=regex_results.get("date", []),
        amounts=regex_results.get("amount", []),
        person_names=persons,
        organisations=orgs,
    )


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    samples = [
        "My order #98765 has not arrived",
        "I need a refund of $49.99 from last month",
        "Please contact me at john.doe@example.com or +1-800-555-1234",
        "Ticket TKT-4421 is still open",
        "I placed my order on 15/06/2024 and still haven't received it",
        "I want to speak to John Smith from your billing team",
        "The Slack integration is broken",
        "just a normal message with nothing in it",
    ]

    for s in samples:
        e = extract_entities(s)
        print(f"\nText    : {s}")
        print(f"Entities: {e.to_dict()}")
