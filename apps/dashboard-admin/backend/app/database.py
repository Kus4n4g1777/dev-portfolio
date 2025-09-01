print(">>>> DATABASE.PY LOADED <<<<")
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
#from dotenv import load_dotenv  # <- import this

# Load the .env file so os.getenv works
#load_dotenv()  # <- this actually reads my  .env


# Construct DATABASE_URL dynamically from separate environment variables
#DB_USER = os.getenv("DB_USER", "default_user")
#DB_PASSWORD = os.getenv("DB_PASSWORD", "default_password")
#DB_HOST = os.getenv("DB_HOST", "db")
#DB_NAME = os.getenv("DB_NAME", "default_db")

# Debug: make sure env vars are actually there
#print(f"DB_USER={DB_USER}, DB_PASSWORD={DB_PASSWORD}, DB_HOST={DB_HOST}, DB_NAME={DB_NAME}")

#if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
#    raise RuntimeError("Missing one of the DB environment variables!")


#SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
# The DATABASE_URL is set in your .env file and provided by Docker
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL") #if no load_dot env no getenv

# --- ADD THIS DEBUG BLOCK ---
print("--- DATABASE DEBUG ---")
print(f"DATABASE_URL from Python: {SQLALCHEMY_DATABASE_URL}")
print(f"Type of SQLALCHEMY_DATABASE_URL: {type(SQLALCHEMY_DATABASE_URL)}")
print("----------------------")
# ---------------------------


# It's good practice to check if the variable was actually found.
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please check your .env file and docker-compose configuration.")

# Create the SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a sessionmaker to create new sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models
Base = declarative_base()

# Dependency to get a new database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
