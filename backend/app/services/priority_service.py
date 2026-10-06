"""
SupportIQ — Priority determination service.

Rules (documented):
  CRITICAL : escalation_request, account_delete + negative sentiment
  HIGH     : billing_refund_request, billing_payment_failed,
             tech_integration_issue, general_complaint + negative strong
  MEDIUM   : billing_plan_cancel, order_cancel, tech_app_not_working,
             account_login_issue
  LOW      : greetings, thanks, farewells, FAQ intents, general info
"""
from __future__ import annotations

import sys
import pathlib

# Allow importing from ml/ package
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from app.models.ticket import TicketPriority

_CRITICAL_INTENTS = {"escalation_request"}
_HIGH_INTENTS = {
    "billing_refund_request",
    "billing_payment_failed",
    "tech_integration_issue",
}
_MEDIUM_INTENTS = {
    "billing_plan_cancel",
    "order_cancel",
    "tech_app_not_working",
    "account_login_issue",
    "account_delete",
}
_LOW_INTENTS = {
    "greetings",
    "thanks",
    "farewells",
    "faq_general",
    "general_info",
    "account_password_reset",
    "order_tracking",
    "product_info",
}


def determine_priority(
    intent_name: str,
    sentiment_label: str,
    sentiment_intensity: str,
    confidence: float,
) -> TicketPriority:
    """
    Determine ticket priority based on intent, sentiment, and confidence.

    Parameters
    ----------
    intent_name        : Classifier-predicted intent string
    sentiment_label    : "positive" | "neutral" | "negative"
    sentiment_intensity: "mild" | "moderate" | "strong"
    confidence         : Model confidence score [0, 1]

    Returns
    -------
    TicketPriority enum value
    """
    is_negative = sentiment_label == "negative"
    is_strong = sentiment_intensity == "strong"

    # CRITICAL: explicit escalation request
    if intent_name in _CRITICAL_INTENTS:
        return TicketPriority.CRITICAL

    # CRITICAL: account deletion with negative strong sentiment
    if intent_name == "account_delete" and is_negative and is_strong:
        return TicketPriority.CRITICAL

    # HIGH: billing / tech issues (or with strong negative)
    if intent_name in _HIGH_INTENTS:
        return TicketPriority.HIGH

    # HIGH: general_complaint with negative sentiment
    if intent_name == "general_complaint" and is_negative:
        return TicketPriority.HIGH

    # MEDIUM: operational issues or medium-severity intents
    if intent_name in _MEDIUM_INTENTS:
        return TicketPriority.MEDIUM

    # MEDIUM: strong negative sentiment on any unclassified intent
    if is_negative and is_strong:
        return TicketPriority.MEDIUM

    # LOW: routine / informational intents
    if intent_name in _LOW_INTENTS:
        return TicketPriority.LOW

    # Default: LOW for everything else
    return TicketPriority.LOW
