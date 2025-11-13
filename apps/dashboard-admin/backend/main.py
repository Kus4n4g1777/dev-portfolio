import os
import jwt
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Annotated
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from auth import create_access_token, verify_password, get_password_hash, verify_access_token, log_login_event  # <--- NEW
from app.database import get_db, engine, Base  # <-- THIS IMPORTS DATABASE.PY
from app.routes import websocket_routes
from datetime import datetime, timedelta

# --------------------------------------------------------------------------------
# Database Configuration
# --------------------------------------------------------------------------------

# Use environment variables from the .env file
# The Docker Compose service name 'db' is used as the hostname.
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@db/{DB_NAME}"

# Create the SQLAlchemy engine.
# `pool_pre_ping` is a setting to ensure the connection is alive.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create a session maker for database interactions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our SQLAlchemy models.
Base = declarative_base()


# --------------------------------------------------------------------------------
# Database Models (SQLAlchemy ORM)
# --------------------------------------------------------------------------------

class User(Base):
    """
    Represents the 'users' table in our database.
    
    This model now includes a 'hashed_password' column for authentication.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, unique=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")


# Dependency to get a database session
def get_db():
    """Provides a database session to a route and closes it afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------------------------------------------------------------------------
# Fast API Application
# --------------------------------------------------------------------------------
app = FastAPI()

@app.get("/health")
def health_check():
    """
    Simple health check endpoint for Docker.
    """
    return {"status": "ok"}

#Include our just created first route (websocket)
app.include_router(websocket_routes.router)

# --- CORS Middleware ---
# This is the key to fixing our network error of cors. This is a white list for access.
# This is the key to fixing our network error of cors. This is a white list for access.
origins = [
    "http://localhost",
    "http://localhost:5173",  # React Vite
    "http://localhost:3001",  # React Docker
    "http://127.0.0.1:5173",  # React Vite
    "http://127.0.0.1:3001",  # React Docker
    "http://10.0.2.2:8000",   # Flutter emulator
    "http://localhost:54712", # Flutter web
    "http://127.0.0.1:8000",  # Flutter turned on because of android studio
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers, including Authorization
)

# --- OAuth2PasswordBearer for protected routes ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# --- Pydantic Models for Request/Response ---
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"


# --- Dependency to get the current user from the token ---
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    """
    Dependency that gets the current user from a JWT token.
    Fetches the user from the database.
    Raises an HTTPException if the token is invalid or the user is not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# --------------------------------------------------------------------------------
# API Endpoints
# --------------------------------------------------------------------------------

@app.post("/token")
async def login_for_access_token(
    request: Request,  # <--- NEW: Add this to get IP address
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """
    Login endpoint to get an access token.
    Checks credentials against the database and returns a JWT token and sets a refresh token in an HttpOnly cookie.
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    # 🎯 LOG THE LOGIN EVENT TO LAMBDA
    client_ip = request.client.host if request.client else "unknown"
    log_login_event(user.username, source_ip=client_ip)
    
    # Set refresh token as HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # True if using HTTPS in production
        samesite="strict",
        max_age=7*24*3600  # 7 days
    )
    
    # Return only access token in JSON
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Protected endpoint to get the current user's information.
    Requires a valid JWT token.
    """
    return {"username": current_user.username, "email": current_user.email, "role": current_user.role}


@app.post("/users/", response_model=None)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Endpoint to create a new user.
    Hashes the password before storing it.
    """
    # Check if a user with the same email or username already exists
    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    # Hash the password and create the new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "User created successfully"}

# Function to create refresh token
def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=7))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm="HS256")


# Refresh token endpoint
@app.post("/refresh")
async def refresh_access_token(response: Response, refresh_token: str = Cookie(None)):
    """
    Takes a valid refresh token from HttpOnly cookie and returns a new access token.
    """
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    
    try:
        payload = jwt.decode(refresh_token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        access_token = create_access_token(data={"sub": username})
        
        # Rotate refresh token
        new_refresh_token = create_refresh_token(data={"sub": username})
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=False,  # True in production with HTTPS
            samesite="strict",
            max_age=7*24*3600
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

