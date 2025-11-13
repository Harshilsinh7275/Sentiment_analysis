# app.py
import streamlit as st
import pandas as pd
from transformers import pipeline
import os

# Load saved model
MODEL_PATH = "saved_model"
st.set_page_config(page_title="Sentiment Analysis POC", layout="wide")

@st.cache_resource
def load_model():
    return pipeline("sentiment-analysis", model=MODEL_PATH, tokenizer=MODEL_PATH)

analyzer = load_model()

# Helper to simplify labels
def simplify_label(label: str) -> str:
    stars = int(label.split()[0])
    if stars <= 2:
        return "Negative 😞"
    elif stars == 3:
        return "Neutral 😐"
    else:
        return "Positive 😊"

st.title("🧠 Sentiment Analysis POC")
st.markdown("Analyze text, `.txt`, or `.csv` files using a fine-tuned multilingual BERT model.")

# --- Input type selection ---
option = st.radio("Choose input type:", ["Single Sentence", "Text File (.txt)", "CSV File (.csv)"])

if option == "Single Sentence":
    text_input = st.text_area("Enter your sentence:", height=120)
    if st.button("Analyze Sentiment"):
        if text_input.strip():
            result = analyzer(text_input)[0]
            sentiment = simplify_label(result["label"])
            st.success(f"**{sentiment}** ({result['label']} with confidence {result['score']:.2f})")
        else:
            st.warning("Please enter some text.")

elif option == "Text File (.txt)":
    uploaded_file = st.file_uploader("Upload your text file", type=["txt"])
    if uploaded_file:
        lines = [line.decode("utf-8").strip() for line in uploaded_file.readlines() if line.strip()]
        if len(lines) == 0:
            st.error("The file is empty!")
        else:
            mode = st.radio("Choose analysis mode:", ["Each line separately", "Overall combined sentiment"])
            if st.button("Analyze File"):
                if mode == "Each line separately":
                    results = analyzer(lines)
                    df = pd.DataFrame({
                        "Text": lines,
                        "Label": [r["label"] for r in results],
                        "Sentiment": [simplify_label(r["label"]) for r in results],
                        "Confidence": [r["score"] for r in results],
                    })
                    st.dataframe(df)
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button("⬇️ Download Results as CSV", data=csv, file_name="sentiment_results.csv")
                else:
                    combined = " ".join(lines)
                    result = analyzer(combined)[0]
                    sentiment = simplify_label(result["label"])
                    st.success(f"**Overall Sentiment:** {sentiment} ({result['label']}, {result['score']:.2f})")

elif option == "CSV File (.csv)":
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Detected columns:", list(df.columns))
        text_col = st.selectbox("Select column to analyze:", df.columns)
        if st.button("Analyze CSV"):
            texts = df[text_col].dropna().astype(str).tolist()
            results = analyzer(texts)
            df["Label"] = [r["label"] for r in results]
            df["Sentiment"] = [simplify_label(r["label"]) for r in results]
            df["Confidence"] = [r["score"] for r in results]
            st.dataframe(df.head(10))
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download Results", data=csv, file_name="sentiment_results.csv")
