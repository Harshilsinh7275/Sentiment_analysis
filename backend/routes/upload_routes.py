from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from ..services import azure_blob_service, db_service
from ..models.file_model import FileMeta
from .auth_routes import get_current_user
from datetime import datetime
from uuid import uuid4

router = APIRouter()


# === Upload a file ===
@router.post("/uploads")
async def upload_user_file(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    """Upload .txt or .csv file to Azure Blob Storage and save metadata in MongoDB."""
    if not (file.filename.endswith(".txt") or file.filename.endswith(".csv")):
        raise HTTPException(status_code=400, detail="Only .txt or .csv files allowed")

    try:
        # Upload to Azure Blob
        upload_result = await azure_blob_service.upload_file_to_blob(
            await file.read(),
            file.filename,
            current_user["email"],
            is_result=False
        )

        # Prepare metadata model
        file_data = FileMeta(
            id=str(uuid4()),
            user_email=current_user["email"],
            file_name=file.filename,
            blob_name=upload_result["blob_name"],
            blob_url=upload_result["url"],
            uploaded_at=datetime.utcnow()
        )

        # Save metadata in MongoDB
        await db_service.save_file_metadata(file_data.dict())

        return {"message": "File uploaded successfully", "file_info": file_data.dict()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === List all uploaded files for current user ===
@router.get("/uploads")
async def list_user_uploads(current_user=Depends(get_current_user)):
    """List all files uploaded by the current user."""
    try:
        files = await db_service.get_user_files(current_user["email"])
        return {"uploads": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Get details for a specific file ===
@router.get("/uploads/{file_id}")
async def get_file_info(file_id: str, current_user=Depends(get_current_user)):
    """Get a specific file’s metadata by ID."""
    file = await db_service.get_file_by_id(file_id)
    if not file or file["user_email"] != current_user["email"]:
        raise HTTPException(status_code=404, detail="File not found or unauthorized")
    return file


@router.delete("/uploads/{file_id}")
async def delete_file(file_id: str, current_user=Depends(get_current_user)):
    """Delete a file from both Azure Blob and MongoDB metadata."""
    try:
        file = await db_service.get_file_by_id(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found in DB")
        if file["user_email"] != current_user["email"]:
            raise HTTPException(status_code=403, detail="Unauthorized access")

        # Try deleting from Azure Blob
        try:
            await azure_blob_service.delete_blob(file["blob_name"])
        except Exception as e:
            print(f" Azure delete failed: {e}")  # don't fail app, just log it

        # Delete metadata from MongoDB
        success = await db_service.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=404, detail="File not found in DB after delete attempt")

        return {"message": f"File {file['file_name']} deleted successfully."}

    except HTTPException:
        raise
    except Exception as e:
        print(f" Unexpected delete error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during file delete")
