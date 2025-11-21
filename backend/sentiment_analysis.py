# backend/sentiment_analysis.py

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Dict, Any

# Lazy load model to prevent startup timeout (especially in Azure)
sentiment_model = None


def get_model():
    global sentiment_model, tokenizer
    if sentiment_model is None:
        model_name = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        sentiment_model = pipeline(
            "sentiment-analysis",
            model=model_name,
            tokenizer=tokenizer
        )
    return sentiment_model



def analyze_text(text: str) -> Dict[str, Any]:
    """
    Analyze the sentiment of a single text string.
    Returns a dict with label and score.
    """
    model = get_model()
    result = model(text)[0]
    return {
        "label": result["label"],
        "score": float(result["score"]),
    }


def analyze_many(texts: List[str]) -> List[Dict[str, Any]]:
    """
    Analyze a list of texts in one go.
    Returns a list of {label, score}.
    """
    if not texts:
        return []

    model = get_model()
    outputs = model(texts)
    return [
        {"label": o["label"], "score": float(o["score"])}
        for o in outputs
    ]


def build_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build file-level summary stats from row-level results.
    """
    total = len(results)
    if total == 0:
        return {
            "total": 0,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "overall": None,
        }

    pos = sum(1 for r in results if r["label"].upper().startswith("POS"))
    neg = sum(1 for r in results if r["label"].upper().startswith("NEG"))
    neu = total - pos - neg

    if pos > neg:
        overall = "POSITIVE"
    elif neg > pos:
        overall = "NEGATIVE"
    else:
        overall = "MIXED"

    return {
        "total": total,
        "positive": pos,
        "negative": neg,
        "neutral": neu,
        "overall": overall,
    }
