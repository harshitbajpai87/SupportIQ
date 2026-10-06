"""
SupportIQ — NLP Text Preprocessor
Handles tokenisation, stopword removal, and stemming for intent classification.
"""

import re
import string
import unicodedata

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize

# ---------------------------------------------------------------------------
# Ensure required NLTK corpora are available (downloaded once)
# ---------------------------------------------------------------------------

_REQUIRED_CORPORA = [
    ("tokenizers/punkt", "punkt"),
    ("tokenizers/punkt_tab", "punkt_tab"),
    ("corpora/stopwords", "stopwords"),
    ("taggers/averaged_perceptron_tagger", "averaged_perceptron_tagger"),
    ("chunkers/maxent_ne_chunker", "maxent_ne_chunker"),
    ("corpora/words", "words"),
]


def ensure_nltk_data() -> None:
    """Download any missing NLTK resources silently."""
    for path, pkg in _REQUIRED_CORPORA:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(pkg, quiet=True)


ensure_nltk_data()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STEMMER = PorterStemmer()
_STOP_WORDS = set(stopwords.words("english"))

# Words that are meaningful for support intent classification and should NOT
# be removed even though they appear in the stopwords list.
_SUPPORT_KEEP_WORDS = {
    "not", "no", "nor", "never", "can't", "cannot", "won't", "don't",
    "doesn't", "didn't", "isn't", "aren't", "wasn't", "weren't",
    "couldn't", "shouldn't", "wouldn't", "haven't", "hasn't", "hadn't",
}
_EFFECTIVE_STOP_WORDS = _STOP_WORDS - _SUPPORT_KEEP_WORDS

# Contraction map — expand before tokenising
_CONTRACTIONS: dict[str, str] = {
    "i'm": "i am",
    "i've": "i have",
    "i'll": "i will",
    "i'd": "i would",
    "you're": "you are",
    "you've": "you have",
    "you'll": "you will",
    "you'd": "you would",
    "he's": "he is",
    "she's": "she is",
    "it's": "it is",
    "we're": "we are",
    "we've": "we have",
    "we'll": "we will",
    "we'd": "we would",
    "they're": "they are",
    "they've": "they have",
    "they'll": "they will",
    "they'd": "they would",
    "can't": "cannot",
    "couldn't": "could not",
    "won't": "will not",
    "wouldn't": "would not",
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "haven't": "have not",
    "hasn't": "has not",
    "hadn't": "had not",
    "shouldn't": "should not",
    "that's": "that is",
    "there's": "there is",
    "what's": "what is",
    "where's": "where is",
    "who's": "who is",
    "let's": "let us",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalise_unicode(text: str) -> str:
    """Convert accented characters to ASCII equivalents."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _expand_contractions(text: str) -> str:
    """Expand English contractions using a lookup table."""
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(k) for k in _CONTRACTIONS) + r")\b",
        flags=re.IGNORECASE,
    )

    def _replace(match: re.Match) -> str:
        token = match.group(0).lower()
        return _CONTRACTIONS.get(token, token)

    return pattern.sub(_replace, text)


def _remove_noise(text: str) -> str:
    """Strip URLs, email addresses, order-number-like tokens, and excess whitespace."""
    # URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    # Email addresses
    text = re.sub(r"\S+@\S+\.\S+", " email ", text)
    # Standalone numbers that are likely order/ticket IDs — keep number semantics
    # but replace with a placeholder token so the vectoriser sees it
    text = re.sub(r"\b\d{5,}\b", " order_number ", text)
    # Multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def clean(text: str) -> str:
    """
    Return a lightly cleaned version of the text (contractions expanded,
    unicode normalised, noise removed) without stemming.  Used when we want
    readable text — e.g. for sentiment analysis.
    """
    text = str(text)
    text = _normalise_unicode(text)
    text = text.lower()
    text = _expand_contractions(text)
    text = _remove_noise(text)
    return text


def preprocess(text: str, stem: bool = True) -> str:
    """
    Full preprocessing pipeline for intent classification:
      1. Unicode normalisation
      2. Lowercase
      3. Contraction expansion
      4. Noise removal (URLs, emails, long numbers)
      5. Punctuation removal
      6. NLTK word tokenisation
      7. Stopword removal (support-aware)
      8. Optional Porter stemming

    Returns a single whitespace-joined string ready for TF-IDF vectorisation.
    """
    text = str(text)
    text = _normalise_unicode(text)
    text = text.lower()
    text = _expand_contractions(text)
    text = _remove_noise(text)

    # Remove punctuation (keep hyphens inside words)
    text = text.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
    text = re.sub(r"\s+", " ", text).strip()

    tokens = word_tokenize(text)

    # Remove stopwords (but preserve negations)
    tokens = [t for t in tokens if t not in _EFFECTIVE_STOP_WORDS and len(t) > 1]

    if stem:
        tokens = [_STEMMER.stem(t) for t in tokens]

    return " ".join(tokens)


def preprocess_batch(texts: list[str], stem: bool = True) -> list[str]:
    """Preprocess a list of texts. Convenience wrapper for training."""
    return [preprocess(t, stem=stem) for t in texts]


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    samples = [
        "I can't log into my account",
        "My payment was declined and I'm very frustrated!!!",
        "Where is my order #98765?",
        "Please reset my password ASAP",
        "Hi, I need help",
    ]
    print(f"{'Original':<55} {'Preprocessed'}")
    print("-" * 100)
    for s in samples:
        print(f"{s:<55} {preprocess(s)}")
