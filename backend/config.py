import os
import ssl
import certifi
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from azure.storage.blob import BlobServiceClient


# LOAD ENV VARIABLES
load_dotenv()

# FIX TLS for Windows
ssl._create_default_https_context = ssl._create_unverified_context


# MONGO DB ATLAS (Users, Files, Results)
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise Exception(" MONGO_URI is missing in .env")

atlas_client = AsyncIOMotorClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=20000
)

atlas_db = atlas_client["sentiment_poc"]

users_collection = atlas_db["users"]
blacklist_collection = atlas_db["blacklist"]
files_collection = atlas_db["files"]
results_collection = atlas_db["results"]  

# JWT CONFIG
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

if not JWT_SECRET:
    raise Exception(" JWT_SECRET missing in .env")


# AZURE BLOB STORAGE
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")

if not AZURE_STORAGE_CONNECTION_STRING:
    raise Exception(" AZURE_STORAGE_CONNECTION_STRING missing in .env")

if not AZURE_CONTAINER_NAME:
    raise Exception(" AZURE_CONTAINER_NAME missing in .env")

blob_service = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
blob_container = blob_service.get_container_client(AZURE_CONTAINER_NAME)
