from fastapi import FastAPI
from pydantic import BaseModel
import joblib

# Load model and vectorizer
model = joblib.load('phishing_model.pkl')
vectorizer = joblib.load('tfidf_vectorizer.pkl')

# Initialize app
app = FastAPI()

# Input format
class EmailInput(BaseModel):
    text: str

# Prediction endpoint
@app.post("/predict")
def predict_email(input: EmailInput):
    # Vectorize the input
    X = vectorizer.transform([input.text])
    # Predict
    prediction = model.predict(X)[0]
    return {"prediction": prediction}
