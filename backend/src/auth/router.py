
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import List, Optional
from pydantic import BaseModel

from src.auth.security import (
    Token, create_access_token, get_current_user, 
    ACCESS_TOKEN_EXPIRE_MINUTES, get_username_hash, verify_password, 
    encrypt_username, decrypt_username
)
from src.auth import service as auth_service

router = APIRouter(prefix="/api", tags=["Auth"])

# Schemas
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"

class UserResponse(BaseModel):
    username: str
    role: str
    id: Optional[int] = None

# --- Endpoints ---

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Authentication Strategy:
    # 1. Try finding by Hash (Secure Users)
    # 2. Try finding by Plain (Legacy Users)
    
    input_hash = get_username_hash(form_data.username)
    
    # Try Hash
    user = auth_service.obtener_usuario_por_username(input_hash)
    
    # Fallback to Plain if not found (Legacy compatibility)
    if not user:
        user = auth_service.obtener_usuario_por_username(form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check password
    if not verify_password(form_data.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Create Token
    sub = user.get('username_hash') or user['username']
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": sub}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    # Pydantic will filter fields if we use a response_model, but returning dict is fine for legacy compat
    return current_user

# Admin Routes

@router.get("/users")
def get_users(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Requires Admin Role")
    
    try:
        df = auth_service.listar_usuarios()
        users = df.fillna("").to_dict(orient="records")
        
        # Decrypt usernames for display
        for u in users:
            if u.get('username_encrypted'):
                try:
                    u['username'] = decrypt_username(u['username_encrypted'])
                except:
                    pass 
            
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users")
def create_new_user(req: UserCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Requires Admin Role")
    
    u_hash = get_username_hash(req.username)
    u_enc = encrypt_username(req.username)
    
    ok, msg = auth_service.crear_usuario(
        username=u_hash, 
        password=req.password, 
        role=req.role,
        username_hash=u_hash,
        username_encrypted=u_enc
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "msg": msg}

@router.delete("/users/{uid}")
def delete_user(uid: int, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Requires Admin Role")
    
    ok, msg = auth_service.eliminar_usuario(uid)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "msg": msg}
