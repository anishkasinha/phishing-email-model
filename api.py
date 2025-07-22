from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import os

app = Flask(__name__)
CORS(app)

model = None
vectorizer = None

def load_model_and_vectorizer():
    global model, vectorizer
    try:
        model = joblib.load('phishing_model.pkl')
        vectorizer = joblib.load('tfidf_vectorizer.pkl')
        print("Model and vectorizer loaded successfully!")
        return True
    except FileNotFoundError as e:
        print(f"Error loading model files: {e}")
        return False

def predict_phishing(email_text):
    if model is None or vectorizer is None:
        return None, None, "Model not loaded"

    try:
        email_tfidf = vectorizer.transform([email_text])
        prediction = model.predict(email_tfidf)[0]
        probability = model.predict_proba(email_tfidf)[0]
        confidence_scores = {
            'safe': float(probability[0]),
            'phishing': float(probability[1])
        }
        return int(prediction), confidence_scores, None
    except Exception as e:
        return None, None, str(e)

@app.route("/", methods=["GET"])
def root():
    model_status = "loaded" if model and vectorizer else "not loaded"
    return jsonify({
        "message": "Phishing Email Detection API is running!",
        "status": "active",
        "model_status": model_status,
        "endpoints": {
            "predict": "POST /predict",
            "health": "GET /health",
            "info": "GET /info"
        }
    })

@app.route("/health", methods=["GET"])
def health():
    model_loaded = model is not None and vectorizer is not None
    return jsonify({
        "status": "healthy" if model_loaded else "unhealthy",
        "model_loaded": model_loaded,
        "vectorizer_loaded": vectorizer is not None,
        "classifier_loaded": model is not None
    })

@app.route("/info", methods=["GET"])
def info():
    return jsonify({
        "api_name": "Phishing Email Detection API",
        "version": "1.0",
        "description": "Detects phishing emails using machine learning",
        "input_format": {
            "method": "POST",
            "endpoint": "/predict",
            "body": {
                "email_text": "Your email content here"
            }
        },
        "output_format": {
            "prediction": "0 (safe) or 1 (phishing)",
            "label": "safe email or phishing email",
            "confidence": {
                "safe": "confidence score for safe classification",
                "phishing": "confidence score for phishing classification"
            }
        }
    })
@app.route("/predict", methods=["POST"])
def predict_route():
    try:
        if model is None or vectorizer is None:
            print("[ERROR] Model or vectorizer not loaded")
            return jsonify({ "error": "Model or vectorizer not loaded" }), 500

        data = request.get_json()
        print("[DEBUG] Raw JSON data:", data)

        if not data:
            return jsonify({ "error": "No JSON received" }), 400

        email_text = data.get('email_text', '')
        if not isinstance(email_text, str):
            return jsonify({ "error": "'email_text' must be a string" }), 400

        email_text = email_text.strip()
        print("[DEBUG] Email text received:", email_text)

        if len(email_text) == 0:
            return jsonify({ "error": "Email text cannot be empty" }), 400

        try:
            email_tfidf = vectorizer.transform([email_text])
        except Exception as e:
            print("[ERROR] TF-IDF transform failed:", e)
            return jsonify({ "error": f"Vectorizer transform failed: {str(e)}" }), 500

        try:
            prediction_raw = model.predict(email_tfidf)[0]

            # Handle string or numeric outputs
            if isinstance(prediction_raw, str):
                prediction = 1 if "phish" in prediction_raw.lower() else 0
            else:
                prediction = int(prediction_raw)

            probability = model.predict_proba(email_tfidf)[0]
        except Exception as e:
            print("[ERROR] Model prediction failed:", e)
            return jsonify({ "error": f"Prediction failed: {str(e)}" }), 500

        confidence = {
            'safe': float(probability[0]),
            'phishing': float(probability[1])
        }

        risk_level = "HIGH" if confidence['phishing'] > 0.7 else "MEDIUM" if confidence['phishing'] > 0.4 else "LOW"

        return jsonify({
            "success": True,
            "prediction": prediction,
            "label": "phishing email" if prediction == 1 else "safe email",
            "confidence": confidence,
            "risk_level": risk_level,
            "details": {
                "email_length": len(email_text),
                "processed": True
            }
        })

    except Exception as e:
        print("[EXCEPTION] Unexpected error in /predict:", str(e))
        return jsonify({ "error": f"Unexpected server error: {str(e)}" }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": ["/", "/health", "/info", "/predict"]
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Method not allowed for this endpoint"
    }), 405

if __name__ == "__main__":
    print("Starting Phishing Email Detection API...")
    if load_model_and_vectorizer():
        print("✓ Model loaded successfully!")
        app.run(debug=True, host='0.0.0.0', port=5000)
        print("Model classes:", model.classes_)
    else:
        print("✗ Failed to load model. Please check model files.")
