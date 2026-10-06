# SupportIQ — Backend

## Setup

```bash
cd supportiq/backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python scripts/train_models.py
```

## ML modules

| File | Purpose |
|---|---|
| `ml/preprocessor.py` | Tokenise, clean, stem |
| `ml/trainer.py` | Train TF-IDF + LR / SVM, save .pkl |
| `ml/classifier.py` | Runtime inference singleton |
| `ml/entity_extractor.py` | Regex + NLTK NER |
| `ml/sentiment.py` | VADER sentiment analysis |
| `ml/evaluator.py` | Metrics, confusion matrix |
| `ml/data/intents.json` | Labelled training data (22 intents) |
| `ml/models/` | Saved .pkl artefacts (git-ignored) |
