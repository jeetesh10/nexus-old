# filepath: /workspaces/nexus/services/bot-service/scripts/seed_db.py
"""
Seed initial models into local MongoDB for development.
Run: python services/bot-service/scripts/seed_db.py
"""
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
MONGO = os.environ.get("MONGO_DB_URL", "mongodb://localhost:27017")
client = MongoClient(MONGO)
db = client.get_database("nexus")

models = [
    {
        "name": "gemini",
        "active": True,
        "description": "Gemini (simulated)",
        "capabilities": {"chat": True},
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "meta": {"provider": "google", "api_key": os.environ.get("GEMINI_API_KEY", "")}
    },
    {
        "name": "groq",
        "active": True,
        "description": "Groq (simulated)",
        "capabilities": {"chat": True},
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "meta": {"provider": "groq", "api_key": os.environ.get("GROQ_API_KEY", "")}
    }
]

db.models.delete_many({})
db.models.insert_many(models)
print("Seeded models collection in nexus.models")
