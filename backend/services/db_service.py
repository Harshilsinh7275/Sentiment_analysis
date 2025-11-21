from typing import List, Optional, Dict, Any
from bson.objectid import ObjectId
from bson.errors import InvalidId
import bcrypt


# IMPORT CORRECT MOTOR COLLECTIONS FROM config.py (ATLAS)
from ..config import (
    users_collection,
    blacklist_collection,
    files_collection,
    results_collection
)

# USER MANAGEMENT
async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    return await users_collection.find_one({"email": email})


async def create_user(name: str, email: str, password: str) -> str:
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    doc = {"name": name, "email": email, "password": hashed_pw}
    result = await users_collection.insert_one(doc)
    return str(result.inserted_id)


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None

    user = await users_collection.find_one({"_id": oid})
    if user:
        user["_id"] = str(user["_id"])
    return user


async def update_user(email: str, updates: Dict[str, Any]) -> bool:
    result = await users_collection.update_one({"email": email}, {"$set": updates})
    return result.modified_count > 0



# TOKEN BLACKLIST
async def is_blacklisted(token: str) -> bool:
    return await blacklist_collection.find_one({"token": token}) is not None


async def add_to_blacklist(token: str) -> None:
    await blacklist_collection.insert_one({"token": token})



# FILE METADATA
async def save_file_metadata(file_meta: Dict[str, Any]) -> str:
    result = await files_collection.insert_one(file_meta)
    return str(result.inserted_id)


async def get_user_files(user_email: str) -> List[Dict[str, Any]]:
    cursor = files_collection.find({"user_email": user_email})
    files = await cursor.to_list(length=1000)

    for f in files:
        f["_id"] = str(f["_id"])
    return files


async def get_file_by_id(file_id: str) -> Optional[Dict[str, Any]]:
    query = {"$or": [{"id": file_id}]}

    try:
        query["$or"].append({"_id": ObjectId(file_id)})
    except InvalidId:
        pass

    file_doc = await files_collection.find_one(query)
    if file_doc:
        file_doc["_id"] = str(file_doc["_id"])
    return file_doc


async def delete_file(file_id: str) -> bool:
    query = {"$or": [{"id": file_id}]}

    try:
        query["$or"].append({"_id": ObjectId(file_id)})
    except InvalidId:
        pass

    result = await files_collection.delete_one(query)
    return result.deleted_count > 0



# ANALYSIS RESULTS (ALSO STORED IN ATLAS)
async def save_analysis_result(result_doc: dict) -> str:
    insert_result = await results_collection.insert_one(result_doc)
    return str(insert_result.inserted_id)


async def get_results_by_user(user_email: str):
    cursor = results_collection.find({"user_email": user_email}).sort("created_at", -1)
    docs = await cursor.to_list(length=1000)

    for d in docs:
        d["_id"] = str(d["_id"])
        if "created_at" in d:
            d["created_at"] = str(d["created_at"])

    return docs

async def get_result_by_id(result_id: str):
    try:
        oid = ObjectId(result_id)
    except:
        return None

    doc = await results_collection.find_one({"_id": oid})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc
