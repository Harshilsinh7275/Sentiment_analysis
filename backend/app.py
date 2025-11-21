from fastapi import FastAPI
from dotenv import load_dotenv, find_dotenv

# Load .env from project root
load_dotenv(find_dotenv(".env", raise_error_if_not_found=False))
print("Loaded .env from project root")

from .routes import auth_routes, upload_routes, analysis_routes

print(">>> LOADING FASTAPI APP V3 <<<")  # DEBUG LINE

app = FastAPI(
    title="Sentiment Analysis POC API ",
    swagger_ui_parameters={"persistAuthorization": True},
)

# ROUTERS
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(upload_routes.router, tags=["File Uploads"])
app.include_router(analysis_routes.router)   # prefix is set INSIDE analysis_routes


@app.get("/")
def root():
    return {
        "message": "Sentiment Analysis Using hugging face Model."
    }
