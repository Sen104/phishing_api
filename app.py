from flask import Flask, request, jsonify 
from flask_cors import CORS
import torch
import os
from datetime import datetime

from model.gmail_message import gmail_messages_collection
from model_loader import load_model, load_vectorizer
from utils.graph_utils import email_to_pyg_graph
from utils.version_tracker import get_model_version

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": [
    "https://mail.google.com",
    "chrome-extension://eefgbpahdglinbadkmmdelfkeclkkbjj"
]}}, supports_credentials=True)

# Setup model and vectorizer
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = load_model(device)
vectorizer = load_vectorizer()
model_info = get_model_version()

# Prediction route with MongoDB logging
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    email_text = data.get("email", "").strip()

    if not email_text.strip():
        return jsonify({
            "prediction": "Unknown",
            "phishing_probability": 0,
            "safe_probability": 0,
            "model_version": model_info["version_hash"],
            "model_last_updated": model_info["last_updated"]
        })

    try:
        graph = email_to_pyg_graph(email_text, label=0, vectorizer=vectorizer)
        graph = graph.to(device)
        batch = torch.zeros(graph.x.size(0), dtype=torch.long).to(device)

        with torch.no_grad():
            out = model(graph.x, graph.edge_index, batch)
            probs = torch.softmax(out, dim=1).squeeze()
            phishing_prob = round(probs[1].item() * 100, 2)
            safe_prob = round(probs[0].item() * 100, 2)
            label = "Phishing" if phishing_prob > safe_prob else "Safe"

        # ✅ Save to MongoDB
        document = {
            "email_text": email_text,
            "prediction": label,
            "phishing_probability": phishing_prob,
            "safe_probability": safe_prob,
            "source": "Gmail",
            "fetched_at": datetime.utcnow()
        }
        gmail_messages_collection.insert_one(document)

        return jsonify({
            "prediction": label,
            "phishing_probability": phishing_prob,
            "safe_probability": safe_prob,
            "model_version": model_info["version_hash"],
            "model_last_updated": model_info["last_updated"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Gmail logging route (for manual logging if needed)
@app.route("/log/gmail", methods=["POST"])
def log_single_gmail_message():
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ["email_text", "prediction", "phishing_probability", "safe_probability"]):
            return {"error": "Missing required fields"}, 400

        document = {
            "email_text": data["email_text"],
            "prediction": data["prediction"],
            "phishing_probability": data["phishing_probability"],
            "safe_probability": data["safe_probability"],
            "source": "Gmail",
            "fetched_at": datetime.utcnow()
        }

        result = gmail_messages_collection.insert_one(document)
        return {"message": "Logged successfully", "id": str(result.inserted_id)}, 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all logged Gmail messages
@app.route("/api/gmail/messages", methods=["GET"])
def get_logged_gmail_messages():
    try:
        messages = list(gmail_messages_collection.find().sort("fetched_at", -1).limit(20))
        for msg in messages:
            msg["_id"] = str(msg["_id"])
        return jsonify({"messages": messages}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Clear Gmail logs
@app.route("/api/gmail/clear", methods=["DELETE"])
def clear_gmail_logs():
    try:
        result = gmail_messages_collection.delete_many({})
        return jsonify({"message": f"Deleted {result.deleted_count} messages."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Start server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
