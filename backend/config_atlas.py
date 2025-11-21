import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

# MongoDB Atlas
ATLAS_URI = os.getenv("MONGO_URI")
ATLAS_DB_NAME = os.getenv("MONGO_DB_NAME")

atlas_client = AsyncIOMotorClient(ATLAS_URI)
atlas_db = atlas_client[ATLAS_DB_NAME]

# Only the analysis service uses this
results_collection = atlas_db["results"]
