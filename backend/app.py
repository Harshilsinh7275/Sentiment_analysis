from fastapi import FastAPI
from .routes import auth_routes, upload_routes  # package-relative import
# backend/app.py
from fastapi import FastAPI
from dotenv import load_dotenv, find_dotenv

# Load .env from project root reliably
load_dotenv(find_dotenv(".env", raise_error_if_not_found=False))

app = FastAPI()

from .routes import auth_routes, upload_routes  # keep package-relative imports

app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(upload_routes.router, prefix="/uploads", tags=["uploads"])

@app.get("/")
def ping():
    return {"status": "ok"}

app = FastAPI(
    title="Sentiment Analysis POC API - Phase 2",
    swagger_ui_parameters={"persistAuthorization": True}
)
print("Loaded .env from project root")
# --- Routers ---
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(upload_routes.router, tags=["File Uploads"])  # <-- added

@app.get("/")
def root():
    return {"message": "Phase 2 Running! Use /docs to test file uploads"}
