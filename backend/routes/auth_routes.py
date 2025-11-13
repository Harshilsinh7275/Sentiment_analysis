from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..models.user_model import UserRegister, UserLogin, UserUpdate
from ..services import db_service, jwt_service
import bcrypt

router = APIRouter()

# 👇 Tell Swagger we use Bearer tokens
bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials

    if await db_service.is_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been invalidated.")

    decoded = jwt_service.decode_access_token(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    user = await db_service.get_user_by_email(decoded["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

@router.post("/register")
async def register(user: UserRegister):
    existing = await db_service.get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")
    await db_service.create_user(user.name, user.email, user.password)
    return {"message": "User registered successfully!"}

@router.post("/login")
async def login(user: UserLogin):
    db_user = await db_service.get_user_by_email(user.email)
    if not db_user or not bcrypt.checkpw(user.password.encode("utf-8"), db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    token = jwt_service.create_access_token({"email": user.email})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/profile")
async def profile(current_user=Depends(get_current_user)):
    return {"name": current_user["name"], "email": current_user["email"]}

@router.put("/profile/update")
async def update_profile(update: UserUpdate, current_user=Depends(get_current_user)):
    data = {}
    if update.name: data["name"] = update.name
    if update.email: data["email"] = update.email
    if update.password:
        data["password"] = bcrypt.hashpw(update.password.encode("utf-8"), bcrypt.gensalt())
    await db_service.update_user(current_user["email"], data)
    return {"message": "Profile updated successfully."}

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    await db_service.add_to_blacklist(token)
    return {"message": "Successfully logged out."}
