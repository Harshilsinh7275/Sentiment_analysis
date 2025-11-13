from transformers import pipeline

# Load the saved model and tokenizer
model_path = "saved_model"

sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model=model_path,
    tokenizer=model_path
)

# Example use
print(sentiment_analyzer("मुझे यह रेस्टोरेंट पसंद है"))
