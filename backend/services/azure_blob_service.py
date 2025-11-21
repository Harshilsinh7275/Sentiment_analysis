from azure.storage.blob.aio import BlobServiceClient
from typing import List
from uuid import uuid4
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

AZURE_CONN_STR = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")

blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONN_STR)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)


async def upload_file_to_blob(content: bytes, filename: str):
    """Upload bytes to Azure Blob Storage."""
    blob_name = f"{uuid4()}_{filename}"
    blob_client = container_client.get_blob_client(blob_name)

    await blob_client.upload_blob(content, overwrite=True)

    blob_url = (
        f"https://{blob_service_client.account_name}.blob.core.windows.net/"
        f"{CONTAINER_NAME}/{blob_name}"
    )

    return {
        "blob_name": blob_name,
        "url": blob_url,
        "uploaded_at": datetime.utcnow(),
    }


async def download_blob_bytes(blob_name: str) -> bytes:
    blob_client = container_client.get_blob_client(blob_name)
    stream = await blob_client.download_blob()
    return await stream.readall()


async def delete_blob(blob_name: str):
    blob_client = container_client.get_blob_client(blob_name)
    await blob_client.delete_blob()


async def list_blobs(prefix: str = None) -> List[str]:
    blob_names = []
    async for blob in container_client.list_blobs(name_starts_with=prefix):
        blob_names.append(blob.name)
    return blob_names
