"""
SupportIQ — Model Evaluator
Loads the saved training report and the active pipeline, runs a full
per-class breakdown, and produces a detailed evaluation summary.

Produces:
  - Overall metrics (accuracy, macro precision/recall/F1)
  - Per-intent metrics table
  - Confusion matrix as a dict (for admin dashboard API)
  - Cross-validation summary
  - Model comparison (LR vs SVM)
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import joblib
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from preprocessor import preprocess_batch
from trainer import load_dataset

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ML_DIR = pathlib.Path(__file__).resolve().parent
_MODELS_DIR = _ML_DIR / "models"
_REPORT_PATH = _MODELS_DIR / "training_report.json"
_LR_PATH = _MODELS_DIR / "lr_pipeline.pkl"
_SVM_PATH = _MODELS_DIR / "svm_pipeline.pkl"
_ACTIVE_PATH = _MODELS_DIR / "active_pipeline.pkl"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_models() -> None:
    for p in [_LR_PATH, _SVM_PATH, _ACTIVE_PATH]:
        if not p.exists():
            raise FileNotFoundError(
                f"Model file not found: {p}\n"
                "Run `python scripts/train_models.py` first."
            )


def _load_test_split() -> tuple[list[str], list[str]]:
    """Recreate the same test split used during training (same random_state)."""
    raw_texts, labels = load_dataset()
    processed = preprocess_batch(raw_texts)
    _, X_test, _, y_test = train_test_split(
        processed, labels, test_size=0.20, random_state=42, stratify=labels
    )
    return X_test, y_test


# ---------------------------------------------------------------------------
# Public evaluation API
# ---------------------------------------------------------------------------


def evaluate_model(model_name: str = "active") -> dict[str, Any]:
    """
    Evaluate a named model on the held-out test set.

    Parameters
    ----------
    model_name : "active" | "lr" | "svm"

    Returns
    -------
    dict with: model_name, overall_metrics, per_intent_metrics,
               confusion_matrix_dict, label_order
    """
    _require_models()

    path_map = {"active": _ACTIVE_PATH, "lr": _LR_PATH, "svm": _SVM_PATH}
    if model_name not in path_map:
        raise ValueError(f"model_name must be one of {list(path_map)}")

    pipeline = joblib.load(path_map[model_name])
    X_test, y_test = _load_test_split()
    y_pred = pipeline.predict(X_test)

    labels_sorted = sorted(set(y_test))

    # Overall metrics
    overall = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision_macro": float(precision_score(y_test, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_test, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
    }

    # Per-intent breakdown
    report_dict = classification_report(
        y_test, y_pred, labels=labels_sorted, output_dict=True, zero_division=0
    )
    per_intent = {
        label: {
            "precision": round(report_dict[label]["precision"], 4),
            "recall": round(report_dict[label]["recall"], 4),
            "f1_score": round(report_dict[label]["f1-score"], 4),
            "support": int(report_dict[label]["support"]),
        }
        for label in labels_sorted
        if label in report_dict
    }

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=labels_sorted)
    cm_dict = {
        "labels": labels_sorted,
        "matrix": cm.tolist(),
    }

    return {
        "model_name": model_name,
        "n_test_samples": len(X_test),
        "overall_metrics": overall,
        "per_intent_metrics": per_intent,
        "confusion_matrix": cm_dict,
    }


def compare_models() -> dict[str, Any]:
    """
    Return a side-by-side comparison of LR vs SVM on the test set,
    plus the stored cross-validation results from training_report.json.
    """
    _require_models()

    lr_eval = evaluate_model("lr")
    svm_eval = evaluate_model("svm")

    cv_data: dict = {}
    if _REPORT_PATH.exists():
        with open(_REPORT_PATH) as f:
            report = json.load(f)
        cv_data = {
            "lr_cv": report.get("lr", {}).get("cv", {}),
            "svm_cv": report.get("svm", {}).get("cv", {}),
            "winner": report.get("winner", "unknown"),
            "n_train": report.get("n_train", 0),
            "n_test": report.get("n_test", 0),
        }

    return {
        "lr": lr_eval["overall_metrics"],
        "svm": svm_eval["overall_metrics"],
        "cv": cv_data,
        "recommendation": cv_data.get("winner", "unknown"),
    }


def full_report(verbose: bool = True) -> dict[str, Any]:
    """
    Print + return a complete evaluation report for both models.
    Used by the admin dashboard API and by the CLI script.
    """
    _require_models()

    comparison = compare_models()
    active_eval = evaluate_model("active")

    if verbose:
        _print_report(comparison, active_eval)

    return {
        "comparison": comparison,
        "active_model_evaluation": active_eval,
    }


# ---------------------------------------------------------------------------
# Pretty printer
# ---------------------------------------------------------------------------


def _print_report(comparison: dict, active_eval: dict) -> None:
    sep = "=" * 68

    print(f"\n{sep}")
    print("  SupportIQ - Model Evaluation Report")
    print(sep)

    print("\n[Model Comparison] (Test Set)")
    print(f"  {'Metric':<25} {'LR':>10}  {'SVM':>10}")
    print("  " + "-" * 48)
    metrics = ["accuracy", "precision_macro", "recall_macro", "f1_macro"]
    for m in metrics:
        lr_val = comparison["lr"].get(m, 0)
        svm_val = comparison["svm"].get(m, 0)
        print(f"  {m:<25} {lr_val:>10.4f}  {svm_val:>10.4f}")

    cv = comparison.get("cv", {})
    if cv:
        print("\n[Cross-Validation] (5-fold, Training Set)")
        for model_key, label in [("lr_cv", "Logistic Regression"), ("svm_cv", "Linear SVM")]:
            if model_key in cv:
                print(f"\n  {label}:")
                for metric, vals in cv[model_key].items():
                    mean = vals.get("mean", 0)
                    std = vals.get("std", 0)
                    print(f"    {metric:<22} {mean:.4f} +/- {std:.4f}")

    print(f"\n[Winner] Active Model: {comparison['recommendation'].upper()}")
    print("\n[Per-Intent Metrics] Active Model (Test Set)")
    print(f"  {'Intent':<35} {'P':>6}  {'R':>6}  {'F1':>6}  {'n':>4}")
    print("  " + "-" * 62)
    for intent, m in sorted(active_eval["per_intent_metrics"].items()):
        print(
            f"  {intent:<35} {m['precision']:>6.3f}  {m['recall']:>6.3f}  "
            f"{m['f1_score']:>6.3f}  {m['support']:>4}"
        )

    overall = active_eval["overall_metrics"]
    print(f"\n  {'Overall (macro)':<35} {overall['precision_macro']:>6.3f}  "
          f"{overall['recall_macro']:>6.3f}  {overall['f1_macro']:>6.3f}  "
          f"{active_eval['n_test_samples']:>4}")
    print(f"\n  Accuracy: {overall['accuracy']:.4f}")
    print(f"\n{sep}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    full_report(verbose=True)
