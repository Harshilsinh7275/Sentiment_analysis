# -*- coding: utf-8 -*-
"""
Sentiment Analysis Utility (Interactive)
--------------------------------
Accepts:
  - Single line input
  - .txt file (one review per line)
  - .csv file (text column)
Asks:
  - Whether to analyze line-by-line OR as one combined overall sentiment
Outputs:
  - Sentiment labels (1–5 stars) and simplified category
"""

import os
import pandas as pd
from transformers import pipeline

# Load multilingual pretrained model
MODEL_NAME = "nlptown/bert-base-multilingual-uncased-sentiment"
sentiment_analyzer = pipeline("sentiment-analysis", model=MODEL_NAME)


def simplify_label(label: str) -> str:
    """Convert star rating (1–5) to Positive/Neutral/Negative"""
    stars = int(label.split()[0])
    if stars <= 2:
        return "Negative"
    elif stars == 3:
        return "Neutral"
    else:
        return "Positive"


def analyze_texts(texts, aggregate=False):
    """Analyze a list of texts; optionally combine for overall sentiment."""
    results = sentiment_analyzer(texts)

    for text, res in zip(texts, results):
        label = res["label"]
        score = res["score"]
        sentiment = simplify_label(label)
        print(f"\nText: {text[:120]}{'...' if len(text) > 120 else ''}")
        print(f" → {label} ({sentiment}) [Confidence: {score:.2f}]")

    # Optional overall sentiment
    if aggregate and len(texts) > 1:
        joined_text = " ".join(texts)
        overall = sentiment_analyzer(joined_text)[0]
        label = overall["label"]
        sentiment = simplify_label(label)
        print("\n=== OVERALL SENTIMENT SUMMARY ===")
        print(f"Combined → {label} ({sentiment}) [Confidence: {overall['score']:.2f}]")

    return results


def analyze_file(file_path):
    """Handle .txt or .csv input files."""
    ext = os.path.splitext(file_path)[1].lower()

    # Ask user how to analyze
    choice = input(
        "\nDo you want to analyze each review separately or combine all into one overall sentiment?\n"
        "Enter 's' for separate or 'o' for overall: "
    ).strip().lower()
    aggregate = choice == "o"

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            print("❌ The file is empty.")
            return
        if aggregate:
            print(f"\nCombining {len(lines)} lines into one overall review...")
            analyze_texts([" ".join(lines)], aggregate=True)
        else:
            print(f"\nAnalyzing {len(lines)} lines separately...")
            analyze_texts(lines)

    elif ext == ".csv":
        df = pd.read_csv(file_path)
        print("\nDetected CSV file:")
        print(f"Columns: {list(df.columns)}")
        col = input("👉 Enter the column name containing the text for sentiment analysis: ").strip()
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in CSV!")
        texts = df[col].dropna().astype(str).tolist()
        if not texts:
            print("❌ The column has no valid text data.")
            return

        if aggregate:
            print(f"\nCombining {len(texts)} rows into one overall review...")
            analyze_texts([" ".join(texts)], aggregate=True)
        else:
            print(f"\nAnalyzing {len(texts)} rows separately...")
            results = sentiment_analyzer(texts)
            df["sentiment_label"] = [r["label"] for r in results]
            df["sentiment"] = [simplify_label(r["label"]) for r in results]
            df["confidence"] = [r["score"] for r in results]
            output_path = "sentiment_results.csv"
            df.to_csv(output_path, index=False)
            print(f"✅ Results saved to {output_path}")
    else:
        print("❌ Unsupported file format. Please provide a .txt or .csv file.")


def main():
    print("=== Sentiment Analysis Utility ===")
    print("You can enter either:")
    print("1️⃣ A sentence directly")
    print("2️⃣ A path to a .txt file")
    print("3️⃣ A path to a .csv file")
    print("----------------------------------")

    user_input = input("Enter your sentence or file path: ").strip()

    if os.path.exists(user_input):
        analyze_file(user_input)
    else:
        analyze_texts([user_input])

# Save model and tokenizer locally for POC reuse
MODEL_SAVE_DIR = "saved_model"

if not os.path.exists(MODEL_SAVE_DIR):
    print(f"\n💾 Saving model and tokenizer to '{MODEL_SAVE_DIR}'...")
    sentiment_analyzer.model.save_pretrained(MODEL_SAVE_DIR)
    sentiment_analyzer.tokenizer.save_pretrained(MODEL_SAVE_DIR)
    print("✅ Model and tokenizer saved successfully!")
else:
    print(f"\nℹ️ Model already exists at '{MODEL_SAVE_DIR}'. Skipping save.")



if __name__ == "__main__":
    main()
