from typing import List, Optional, Dict, Any
from bson.objectid import ObjectId
import bcrypt
from ..config import users_collection, blacklist_collection, files_collection  # motor collections

# === User helpers ===

async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    return await users_collection.find_one({"email": email})


async def create_user(name: str, email: str, password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    doc = {"name": name, "email": email, "password": hashed}
    result = await users_collection.insert_one(doc)
    return str(result.inserted_id)


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    return await users_collection.find_one({"_id": oid})


async def update_user(email: str, updates: Dict[str, Any]) -> bool:
    result = await users_collection.update_one({"email": email}, {"$set": updates})
    return result.modified_count > 0


# === Token blacklist ===

async def is_blacklisted(token: str) -> bool:
    doc = await blacklist_collection.find_one({"token": token})
    return doc is not None


async def add_to_blacklist(token: str) -> None:
    await blacklist_collection.insert_one({"token": token})


# === File metadata helpers ===

async def save_file_metadata(file_meta: Dict[str, Any]) -> str:
    """Save uploaded file info (user_email, filename, Azure blob URL, etc.)"""
    result = await files_collection.insert_one(file_meta)
    return str(result.inserted_id)


async def get_user_files(user_email: str) -> List[Dict[str, Any]]:
    """Return list of uploaded files for a user."""
    cursor = files_collection.find({"user_email": user_email})
    files = await cursor.to_list(length=1000)

    # Convert ObjectIds to strings
    for f in files:
        f["_id"] = str(f["_id"])
    return files



from bson.objectid import ObjectId
from bson.errors import InvalidId

async def get_file_by_id(file_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a file by either its MongoDB _id or custom id field."""
    # Build a query that checks both
    query = {"$or": [{"id": file_id}]}

    # If file_id looks like a valid ObjectId, also search by _id
    try:
        query["$or"].append({"_id": ObjectId(file_id)})
    except InvalidId:
        pass  # Ignore if not valid ObjectId

    doc = await files_collection.find_one(query)
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


from bson.errors import InvalidId
from bson.objectid import ObjectId

async def delete_file(file_id: str) -> bool:
    """Delete file by either Mongo _id or custom UUID id."""
    query = {"$or": [{"id": file_id}]}

    try:
        query["$or"].append({"_id": ObjectId(file_id)})
    except InvalidId:
        pass  # Ignore if not a valid ObjectId

    result = await files_collection.delete_one(query)
    return result.deleted_count > 0

