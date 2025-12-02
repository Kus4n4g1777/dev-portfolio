from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

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

class DetectionStatus(enum.Enum):
    """Enum for detection status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class DetectionResult(Base):
    """Stores detection results with metadata"""
    __tablename__ = "detection_results"
    
    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String, nullable=True)
    model_version = Column(String, index=True, nullable=False)
    status = Column(SQLEnum(DetectionStatus), default=DetectionStatus.PENDING)
    total_detections = Column(Integer, default=0)
    avg_confidence = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to metrics (one-to-one)
    metrics = relationship("DetectionMetrics", back_populates="detection", uselist=False)
    # Relationship to bounding boxes (one-to-many)
    bounding_boxes = relationship("BoundingBox", back_populates="detection")

class DetectionMetrics(Base):
    """Stores performance metrics for detections"""
    __tablename__ = "detection_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detection_results.id"), unique=True)
    inference_time_ms = Column(Float, nullable=True)
    preprocessing_time_ms = Column(Float, nullable=True)
    
    detection = relationship("DetectionResult", back_populates="metrics")

class BoundingBox(Base):
    """Stores individual bounding boxes"""
    __tablename__ = "bounding_boxes"
    
    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detection_results.id", ondelete="CASCADE"))
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    label = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    
    # Relationship back to detection
    detection = relationship("DetectionResult", back_populates="bounding_boxes")


