import ssl
import certifi
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Force TLS context fix for Windows / Atlas handshake
ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = AsyncIOMotorClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=20000
)

# --- Database Name ---
db = client["sentiment_poc"]

# --- Collections ---
users_collection = db["users"]
blacklist_collection = db["blacklist"]
files_collection = db["files"]
results_collection = db["results"]

# --- JWT ---
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

# --- Azure ---
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")
