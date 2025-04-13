import certifi
from pymongo import MongoClient
from datetime import datetime
import requests
import torch

from model_loader import load_model, load_vectorizer
from utils.graph_utils import email_to_pyg_graph
from utils.version_tracker import get_model_version

# ✅ MongoDB Atlas Connection
client = MongoClient(
    "mongodb+srv://phishuser:chan123uthi@phishguardclluster.xxfhlcp.mongodb.net/?retryWrites=true&w=majority&appName=PhishGuardClluster",
    tls=True,
    tlsCAFile=certifi.where()
)

db = client["phishing_db"]
gmail_messages_collection = db["gmail_messages"]

# ✅ Load model & version
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = load_model(device)
vectorizer = load_vectorizer()
model_version_info = get_model_version()

# ✅ Gmail Message Logger (Smart logging with model version check)
def save_gmail_messages(messages, access_token=None):
    for msg in messages:
        try:
            msg_id = msg.get("id")
            if not msg_id:
                continue

            # Check existing record
            existing = gmail_messages_collection.find_one({"id": msg_id})
            if existing and existing.get("model_version") == model_version_info["version_hash"]:
                continue  # ✅ Skip if already predicted with same version

            # Fetch full content
            email_text = "N/A"
            if access_token:
                gmail_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=full"
                headers = {"Authorization": f"Bearer {access_token}"}
                res = requests.get(gmail_url, headers=headers)
                if res.ok:
                    payload = res.json()
                    parts = payload.get("payload", {}).get("parts", [])
                    for part in parts:
                        if part.get("mimeType") == "text/plain":
                            from base64 import urlsafe_b64decode
                            email_text = urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                            break

            # Handle N/A or empty emails
            if not email_text.strip() or email_text.strip().lower() == "n/a":
                prediction = "Unknown"
                phishing_prob = 0
                safe_prob = 0
            else:
                graph = email_to_pyg_graph(email_text, label=0, vectorizer=vectorizer)
                graph = graph.to(device)
                batch = torch.zeros(graph.x.size(0), dtype=torch.long).to(device)
                with torch.no_grad():
                    out = model(graph.x, graph.edge_index, batch)
                    probs = torch.softmax(out, dim=1).squeeze()
                    phishing_prob = round(probs[1].item() * 100, 2)
                    safe_prob = round(probs[0].item() * 100, 2)
                    prediction = "Phishing" if phishing_prob > safe_prob else "Safe"

            # ✅ Save or update log
            gmail_messages_collection.update_one(
                {"id": msg_id},
                {
                    "$set": {
                        "threadId": msg.get("threadId"),
                        "email_text": email_text,
                        "prediction": prediction,
                        "phishing_probability": phishing_prob,
                        "safe_probability": safe_prob,
                        "fetched_at": datetime.utcnow(),
                        "model_version": model_version_info["version_hash"]
                    }
                },
                upsert=True  # ✅ Create if not exists
            )

        except Exception as e:
            print("❌ Error processing message:", e)

    return True
