"""
SupportIQ - Model Trainer
Trains TF-IDF + Logistic Regression and TF-IDF + Linear SVM classifiers,
compares them by macro-F1 on a held-out test split, and saves the winner.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
import warnings
from typing import Any

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

# Project-local import (works when run from supportiq/backend/ or via scripts/)
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from preprocessor import preprocess_batch

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ML_DIR = pathlib.Path(__file__).resolve().parent
_DATA_PATH = _ML_DIR / "data" / "intents.json"
_MODELS_DIR = _ML_DIR / "models"
_MODELS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------


def load_dataset(data_path: pathlib.Path = _DATA_PATH) -> tuple[list[str], list[str]]:
    """
    Load intents.json and return parallel lists (texts, labels).
    Each sample in intent["samples"] is labelled with intent["name"].
    """
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)

    texts: list[str] = []
    labels: list[str] = []

    for intent in data["intents"]:
        name = intent["name"]
        for sample in intent["samples"]:
            texts.append(sample)
            labels.append(name)

    return texts, labels


def load_intent_metadata(data_path: pathlib.Path = _DATA_PATH) -> dict[str, dict]:
    """Return a dict mapping intent name -> metadata (response_template, etc.)."""
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    return {
        intent["name"]: {
            "category": intent["category"],
            "description": intent["description"],
            "requires_escalation": intent["requires_escalation"],
            "priority_level": intent["priority_level"],
            "response_template": intent["response_template"],
        }
        for intent in data["intents"]
    }


# ---------------------------------------------------------------------------
# Pipeline builders
# ---------------------------------------------------------------------------


def _build_tfidf() -> TfidfVectorizer:
    """Shared TF-IDF vectoriser configuration."""
    return TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=8000,
        sublinear_tf=True,      # apply 1 + log(tf) scaling
        min_df=1,
        analyzer="word",
    )


def build_lr_pipeline() -> Pipeline:
    """TF-IDF + Logistic Regression pipeline."""
    return Pipeline([
        ("tfidf", _build_tfidf()),
        ("clf", LogisticRegression(
            C=1.0,
            max_iter=1000,
            solver="lbfgs",
            random_state=42,
        )),
    ])


def build_svm_pipeline() -> Pipeline:
    """
    TF-IDF + Linear SVM pipeline.
    LinearSVC does not support predict_proba natively, so we wrap it in
    CalibratedClassifierCV (Platt scaling) to get probability estimates.
    """
    svc = CalibratedClassifierCV(
        LinearSVC(C=1.0, max_iter=2000, random_state=42),
        cv=3,
    )
    return Pipeline([
        ("tfidf", _build_tfidf()),
        ("clf", svc),
    ])


# ---------------------------------------------------------------------------
# Training + evaluation
# ---------------------------------------------------------------------------


def cross_validate_pipeline(
    pipeline: Pipeline,
    X: list[str],
    y: list[str],
    n_splits: int = 5,
) -> dict[str, float]:
    """
    Run stratified k-fold cross-validation and return mean +/- std for
    accuracy, macro-precision, macro-recall, and macro-F1.
    """
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    scoring = {
        "accuracy": "accuracy",
        "precision_macro": "precision_macro",
        "recall_macro": "recall_macro",
        "f1_macro": "f1_macro",
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        results = cross_validate(pipeline, X, y, cv=cv, scoring=scoring, n_jobs=-1)
    return {
        metric: {
            "mean": float(np.mean(results[f"test_{metric}"])),
            "std": float(np.std(results[f"test_{metric}"])),
        }
        for metric in scoring
    }


def train_and_evaluate(
    verbose: bool = True,
) -> dict[str, Any]:
    """
    Full training run:
      1. Load + preprocess dataset
      2. Stratified 80/20 train/test split
      3. Train LR and SVM pipelines
      4. 5-fold CV on training set
      5. Evaluate both on held-out test set
      6. Save the better model (by test macro-F1)
      7. Also save the losing model under its own name for comparison
      8. Return a results dict with all metrics

    Returns
    -------
    dict with keys: lr_cv, svm_cv, lr_test, svm_test, winner,
                    label_classes, intent_metadata, model_paths
    """
    from sklearn.metrics import classification_report

    if verbose:
        print("=" * 60)
        print("SupportIQ - Intent Classifier Training")
        print("=" * 60)

    # ------------------------------------------------------------------
    # 1. Load and preprocess
    # ------------------------------------------------------------------
    if verbose:
        print("\n[1/5] Loading dataset ...")
    raw_texts, labels = load_dataset()
    if verbose:
        print(f"      {len(raw_texts)} samples across {len(set(labels))} intents")

    if verbose:
        print("[2/5] Preprocessing text ...")
    t0 = time.time()
    processed_texts = preprocess_batch(raw_texts)
    if verbose:
        print(f"      Done in {time.time() - t0:.2f}s")

    # ------------------------------------------------------------------
    # 2. Train / test split
    # ------------------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        processed_texts, labels, test_size=0.20, random_state=42, stratify=labels
    )
    if verbose:
        print(f"      Train: {len(X_train)} | Test: {len(X_test)}")

    # ------------------------------------------------------------------
    # 3. Build pipelines
    # ------------------------------------------------------------------
    lr_pipeline = build_lr_pipeline()
    svm_pipeline = build_svm_pipeline()

    # ------------------------------------------------------------------
    # 4. Cross-validation on training data
    # ------------------------------------------------------------------
    if verbose:
        print("\n[3/5] 5-fold cross-validation ...")
        print("      Logistic Regression ...")
    lr_cv = cross_validate_pipeline(lr_pipeline, X_train, y_train)

    if verbose:
        print("      Linear SVM ...")
    svm_cv = cross_validate_pipeline(svm_pipeline, X_train, y_train)

    if verbose:
        _print_cv_results("Logistic Regression", lr_cv)
        _print_cv_results("Linear SVM", svm_cv)

    # ------------------------------------------------------------------
    # 5. Fit on full training set and evaluate on test set
    # ------------------------------------------------------------------
    if verbose:
        print("\n[4/5] Training on full training set ...")

    lr_pipeline.fit(X_train, y_train)
    svm_pipeline.fit(X_train, y_train)

    lr_test_metrics = _evaluate_on_test(lr_pipeline, X_test, y_test)
    svm_test_metrics = _evaluate_on_test(svm_pipeline, X_test, y_test)

    lr_report = classification_report(y_test, lr_pipeline.predict(X_test), output_dict=True)
    svm_report = classification_report(y_test, svm_pipeline.predict(X_test), output_dict=True)

    if verbose:
        print("\n  Logistic Regression - Test Set:")
        _print_test_metrics(lr_test_metrics)
        print("\n  Linear SVM - Test Set:")
        _print_test_metrics(svm_test_metrics)

    # ------------------------------------------------------------------
    # 6. Save models + determine winner
    # ------------------------------------------------------------------
    if verbose:
        print("\n[5/5] Saving models ...")

    lr_f1 = lr_test_metrics["f1_macro"]
    svm_f1 = svm_test_metrics["f1_macro"]
    winner = "svm" if svm_f1 >= lr_f1 else "lr"

    lr_path = _MODELS_DIR / "lr_pipeline.pkl"
    svm_path = _MODELS_DIR / "svm_pipeline.pkl"
    winner_path = _MODELS_DIR / "active_pipeline.pkl"
    metadata_path = _MODELS_DIR / "intent_metadata.json"
    classes_path = _MODELS_DIR / "label_classes.json"

    joblib.dump(lr_pipeline, lr_path)
    joblib.dump(svm_pipeline, svm_path)
    joblib.dump(lr_pipeline if winner == "lr" else svm_pipeline, winner_path)

    classes = sorted(set(labels))
    with open(classes_path, "w") as f:
        json.dump(classes, f, indent=2)

    intent_meta = load_intent_metadata()
    with open(metadata_path, "w") as f:
        json.dump(intent_meta, f, indent=2)

    if verbose:
        print(f"      LR pipeline  -> {lr_path}")
        print(f"      SVM pipeline -> {svm_path}")
        print(f"      Active model -> {winner.upper()} (macro-F1: {max(lr_f1, svm_f1):.4f})")
        print(f"      -> {winner_path}")
        print("\n[OK] Training complete.")
        print("=" * 60)

    # Save full metrics report
    report = {
        "lr": {
            "cv": lr_cv,
            "test": lr_test_metrics,
            "classification_report": lr_report,
        },
        "svm": {
            "cv": svm_cv,
            "test": svm_test_metrics,
            "classification_report": svm_report,
        },
        "winner": winner,
        "winner_f1_macro": float(max(lr_f1, svm_f1)),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "n_intents": len(classes),
        "label_classes": classes,
    }

    report_path = _MODELS_DIR / "training_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report


# ---------------------------------------------------------------------------
# Internal formatting helpers
# ---------------------------------------------------------------------------


def _evaluate_on_test(pipeline: Pipeline, X_test: list[str], y_test: list[str]) -> dict:
    from sklearn.metrics import (
        accuracy_score,
        f1_score,
        precision_score,
        recall_score,
    )

    y_pred = pipeline.predict(X_test)
    return {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision_macro": float(precision_score(y_test, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_test, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
    }


def _print_cv_results(name: str, cv: dict) -> None:
    print(f"\n  {name} - 5-fold CV:")
    for metric, vals in cv.items():
        print(f"    {metric:<22} {vals['mean']:.4f} +/- {vals['std']:.4f}")


def _print_test_metrics(m: dict) -> None:
    for k, v in m.items():
        print(f"    {k:<22} {v:.4f}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    train_and_evaluate(verbose=True)
