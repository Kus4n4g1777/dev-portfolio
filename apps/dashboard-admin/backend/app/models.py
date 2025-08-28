from sqlalchemy import Column, Integer, String
from .database import Base

class User(Base):
    """
    SQLAlchemy model for the 'users' table.
    This defines the structure of the database table.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)
