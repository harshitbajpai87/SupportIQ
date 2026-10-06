"""
SupportIQ — Training Entry Point
Run this script to train models, evaluate them, and save all artefacts.

Usage (from supportiq/backend/):
    python scripts/train_models.py
    python scripts/train_models.py --evaluate-only
    python scripts/train_models.py --no-verbose
"""

from __future__ import annotations

import argparse
import pathlib
import sys

# Make ml/ importable regardless of cwd
_BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
sys.path.insert(0, str(_BACKEND_DIR / "ml"))


def main() -> None:
    parser = argparse.ArgumentParser(description="SupportIQ model trainer")
    parser.add_argument(
        "--evaluate-only",
        action="store_true",
        help="Skip training; run evaluator on existing saved models",
    )
    parser.add_argument(
        "--no-verbose",
        action="store_true",
        help="Suppress detailed output",
    )
    args = parser.parse_args()

    verbose = not args.no_verbose

    if args.evaluate_only:
        print("Running evaluation on existing models …\n")
        from ml.evaluator import full_report
        full_report(verbose=verbose)
    else:
        from ml.trainer import train_and_evaluate
        train_and_evaluate(verbose=verbose)

        print("\nRunning post-training evaluation …\n")
        from ml.evaluator import full_report
        full_report(verbose=verbose)


if __name__ == "__main__":
    main()
