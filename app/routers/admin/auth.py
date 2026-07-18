from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core import security
from app.db import get_db

router = APIRouter(prefix="/admin/auth", tags=["admin"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    user = await get_db().admin_users.find_one({"email": payload.email.lower()})
    if not user or not security.verificar_password(payload.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales invalidas")
    if not user.get("activo", True):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuario desactivado")
    return LoginResponse(
        access_token=security.crear_access_token(user["email"], user.get("rol", "admin"))
    )
