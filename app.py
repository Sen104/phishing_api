from flask import Flask, request, jsonify
import torch
from model_loader import load_model, load_vectorizer
from utils.graph_utils import email_to_pyg_graph
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)


# Setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = load_model(device)
vectorizer = load_vectorizer()

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    email_text = data.get("email")

    if not email_text:
        return jsonify({"error": "Email text is required"}), 400

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

        return jsonify({
            "prediction": label,
            "phishing_probability": phishing_prob,
            "safe_probability": safe_prob
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

