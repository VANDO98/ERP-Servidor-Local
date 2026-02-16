
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
import hashlib
from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

# Configuration (Should ideally be in .env)
SECRET_KEY = "tu-clave-secreta-super-segura-cambiar-en-produccion-12345"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Can be imported by main.py
FERNET_KEY = b'Z7qJqU4y7r7w-2n3b4c5d6e7f8g9h0i1j2k3l4m5n6o=' 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

# Models for Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Security Helpers
def get_username_hash(username: str) -> str:
    """Deterministic hash for searching"""
    return hashlib.sha256(username.encode()).hexdigest()

def encrypt_username(username: str) -> str:
    """Reversible encryption for storage"""
    f = Fernet(FERNET_KEY)
    return f.encrypt(username.encode()).decode()

def decrypt_username(encrypted_username: str) -> str:
    """Decrypt to show real name"""
    try:
        f = Fernet(FERNET_KEY)
        return f.decrypt(encrypted_username.encode()).decode()
    except Exception:
        return "[Error Decrypting]"

# Hashing Functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies password against hash using bcrypt"""
    try:
        plain_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hash_bytes)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Generates bcrypt hash of password"""
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

# JWT Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency to get current user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # Import here to avoid circular dependency if possible, or use a service
    # Ideally should call a service function, but we can do a direct DB call via service
    # to avoid importing the whole monolith.
    from src.auth.service import obtener_usuario_por_username_internal
    
    user = obtener_usuario_por_username_internal(token_data.username)
    
    if user is None:
        raise credentials_exception
        
    # Decrypt username if encrypted field exists
    if user.get('username_encrypted'):
        user['username'] = decrypt_username(user['username_encrypted'])
        
    return user
