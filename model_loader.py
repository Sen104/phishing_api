import torch
import joblib
from model.gnn_model import GCNClassifier  # This is the model you just created

def load_model(device):
    model = GCNClassifier(input_dim=300, hidden_dim=64, num_classes=2)  # Match your trained model's settings
    model.load_state_dict(torch.load("model/phishing_gnn_model.pt", map_location=device))
    model.to(device)
    model.eval()
    return model

def load_vectorizer():
    return joblib.load("model/tfidf_vectorizer.pkl")
