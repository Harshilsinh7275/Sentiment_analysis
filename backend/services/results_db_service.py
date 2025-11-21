from datetime import datetime
from ..config_atlas import results_collection


async def save_result_metadata(user_email: str, analysis_type: str, file_name: str, result_url: str):
    doc = {
        "user_email": user_email,
        "analysis_type": analysis_type,
        "file_name": file_name,
        "result_url": result_url,
        "created_at": datetime.utcnow()
    }
    await results_collection.insert_one(doc)


async def get_results_by_user(user_email: str):
    cursor = results_collection.find({"user_email": user_email}).sort("created_at", -1)
    docs = await cursor.to_list(length=1000)

    for d in docs:
        d["_id"] = str(d["_id"])
        d["created_at"] = str(d["created_at"])

    return docs
