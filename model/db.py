from pymongo import MongoClient
import certifi

client = MongoClient(
    "mongodb+srv://phishuser:chan123uthi@phishguardclluster.xxfhlcp.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsCAFile=" + certifi.where()
)

db = client["phishing_db"]
gmail_messages_collection = db["gmail_messages"]
