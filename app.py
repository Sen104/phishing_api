from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# ✅ Allow Gmail and Chrome Extension access
CORS(app, origins=[
    "https://mail.google.com",
    "chrome-extension://<YOUR_EXTENSION_ID>",  # Replace this with your actual ID
    "https://shield-comms-fyp-t69w.vercel.app"  # Optional: if using Vercel frontend
])

# ✅ DUMMY ML PREDICTION ROUTE
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    email_text = data.get("email_text", "").strip()

    if not email_text or email_text.lower() == "n/a":
        return jsonify({
            "prediction": "Unknown",
            "phishing_probability": 0,
            "safe_probability": 0
        })

    # 🔄 Replace this block with your actual model inference later
    return jsonify({
        "prediction": "Phishing",
        "phishing_probability": 72.3,
        "safe_probability": 27.7
    })

# ✅ VERSION ROUTE FOR MODEL VERSION TRACKING
@app.route("/version", methods=["GET"])
def version():
    return jsonify({
        "version_hash": "v1.0.0"  # Replace with actual hash logic if needed
    })

# ✅ Optional health check
@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "ShieldComms API is live 🚀"})

# ✅ Run locally for testing (optional)
if __name__ == "__main__":
    app.run(debug=True)
