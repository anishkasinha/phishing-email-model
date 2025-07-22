from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

model = None
vectorizer = None

def load_model_and_vectorizer():
    global model, vectorizer
    try:
        model = joblib.load('phishing_model.pkl')
        vectorizer = joblib.load('tfidf_vectorizer.pkl')
        print("Model and vectorizer loaded successfully!")
        print("Model classes:", model.classes_)
        return True
    except FileNotFoundError as e:
        print(f"Error loading model files: {e}")
        print("Make sure 'phishing_model.pkl' and 'tfidf_vectorizer.pkl' are in the same directory as this script")
        return False

def predict_phishing(email_text):
    if model is None or vectorizer is None:
        return None, None, "Model not loaded"

    try:
        email_tfidf = vectorizer.transform([email_text])
        prediction = model.predict(email_tfidf)[0]  # 0 or 1
        probability = model.predict_proba(email_tfidf)[0]  # e.g. [0.8, 0.2]

        confidence_scores = {
            'safe': float(probability[0]),
            'phishing': float(probability[1])
        }

        return int(prediction), confidence_scores, None
    except Exception as e:
        return None, None, str(e)

@app.route("/", methods=["GET"])
def root():
    model_status = "loaded" if model is not None and vectorizer is not None else "not loaded"
    return jsonify({
        "message": "Phishing Email Detection API is running!",
        "status": "active",
        "model_status": model_status,
        "endpoints": {
            "predict": "POST /predict - Send email text to get phishing prediction",
            "health": "GET /health - Check API health",
            "info": "GET /info - Get API information"
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
def predict():
    try:
        if model is None or vectorizer is None:
            return jsonify({"error": "Model not loaded. Please check server logs."}), 500

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided. Please send email text in JSON format."}), 400

        email_text = data.get('email_text', '')
        if not email_text or not isinstance(email_text, str) or len(email_text.strip()) == 0:
            return jsonify({"error": "Invalid or empty 'email_text' field."}), 400

        prediction, confidence, error = predict_phishing(email_text)
        if error:
            return jsonify({"error": f"Prediction failed: {error}"}), 500

        phishing_confidence = confidence.get('phishing', 0)
        if phishing_confidence >= 0.7:
            risk_level = "HIGH"
        elif phishing_confidence >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        label = "phishing email" if prediction == 1 else "safe email"

        return jsonify({
            "success": True,
            "prediction": prediction,
            "label": label,
            "confidence": confidence,
            "risk_level": risk_level,
            "details": {
                "email_length": len(email_text),
                "processed": True
            }
        })

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

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
    print("Loading model and vectorizer...")

    if load_model_and_vectorizer():
        print("✓ Model loaded successfully!")
        print("✓ Starting Flask server...")
        print("API will be available at: http://127.0.0.1:5000")
        print("\nEndpoints:")
        print("- GET  /        - API info")
        print("- GET  /health  - Health check")
        print("- GET  /info    - Detailed API info")
        print("- POST /predict - Make predictions")
        app.run(debug=True, host='0.0.0.0', port=5000)
        print("Model classes:", model.classes_)
    else:
        print("✗ Failed to load model. Please run your training script first to generate the model files.")
