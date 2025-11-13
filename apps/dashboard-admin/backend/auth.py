from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os
import requests  # <--- NEW
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Configuration for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# AWS Lambda configuration
LAMBDA_URL = os.getenv("LAMBDA_URL")  # <--- NEW: We'll set this in .env

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set. Please set it in your .env file.")

# --- Password Hashing Functions ---
def verify_password(plain_password, hashed_password):
    """Verifies a plain-text password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hashes a plain-text password."""
    return pwd_context.hash(password)

# --- JWT Token Functions ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str):
    """Verifies a JWT token and returns the payload if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# --- NEW: Lambda Logging Function ---
def log_login_event(username: str, source_ip: str = "unknown"):
    """
    Sends a login event to AWS Lambda for logging in DynamoDB.
    This is a fire-and-forget operation with a short timeout.
    """
    if not LAMBDA_URL:
        logger.warning("LAMBDA_URL not set. Skipping login event logging.")
        return
    
    try:
        payload = {
            "username": username,
            "sourceIp": source_ip  # Optional: pass the user's IP
        }
        
        # Fire-and-forget with 2 second timeout
        response = requests.post(
            LAMBDA_URL,
            json=payload,
            timeout=2
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully logged login event for user: {username}")
        else:
            logger.warning(f"Lambda returned status {response.status_code}: {response.text}")
    
    except requests.exceptions.Timeout:
        logger.warning(f"Lambda call timed out for user: {username}")
    except Exception as e:
        logger.error(f"Error calling Lambda for user {username}: {str(e)}")