from pydantic import BaseModel
from datetime import datetime

class FileMeta(BaseModel):
    id: str
    user_email: str
    file_name: str
    blob_name: str
    blob_url: str
    uploaded_at: datetime
