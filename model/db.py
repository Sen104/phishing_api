from pymongo import MongoClient
import certifi

# ✅ Use your working URI directly (no need for os.getenv during deployment rush)
MONGODB_URI = "mongodb+srv://phishuser:chan123uthi@phishguardclluster.xxfhlcp.mongodb.net/?retryWrites=true&w=majority&tls=true"

# ✅ Connect using TLS with certifi CA bundle
client = MongoClient(
    MONGODB_URI,
    tls=True,
    tlsAllowInvalidCertificates=False,
    tlsCAFile=certifi.where()
)

# ✅ Use phishing_db and collection
db = client["phishing_db"]
gmail_messages_collection = db["gmail_messages"]
