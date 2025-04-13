from pymongo import MongoClient
import certifi
import os

# ✅ Replace with your actual MongoDB URI if not using env variable
MONGODB_URI = os.getenv("MONGODB_URI", "your-mongodb+srv-uri")

# ✅ Connect using TLS/SSL with certifi bundle
client = MongoClient(MONGODB_URI, tls=True, tlsCAFile=certifi.where())

# ✅ Use phishing database
db = client["phishing_db"]
gmail_messages_collection = db["gmail_messages"]
