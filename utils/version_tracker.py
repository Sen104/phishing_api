import os
import hashlib
from datetime import datetime

# Path to your model file 
MODEL_PATH = "model/saved_model.pth"

# Ensure the directory exists
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

def get_model_version(model_path=MODEL_PATH):
    if not os.path.exists(model_path):
        return {
            "version_hash": "N/A",
            "last_updated": "N/A"
        }

    # Read and hash the model file
    with open(model_path, "rb") as f:
        model_bytes = f.read()
        version_hash = hashlib.sha256(model_bytes).hexdigest()

    # Get last modified time
    last_modified = os.path.getmtime(model_path)
    last_updated = datetime.fromtimestamp(last_modified).isoformat()

    return {
        "version_hash": version_hash[:12],  # Short hash
        "last_updated": last_updated
    }
