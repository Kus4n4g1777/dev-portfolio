from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class DetectionStatus(str, Enum):
    """Enum for detection status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

# ----- INPUT DTOs (What client sends to server) -----

class BoundingBoxDTO(BaseModel):
    """Single bounding box with validation"""
    x1: float = Field(ge=0.0, le=1.0, description="Top-left x (normalized)")
    y1: float = Field(ge=0.0, le=1.0, description="Top-left y (normalized)")
    x2: float = Field(ge=0.0, le=1.0, description="Bottom-right x (normalized)")
    y2: float = Field(ge=0.0, le=1.0, description="Bottom-right y (normalized)")
    label: str = Field(min_length=1, max_length=50)
    confidence: float = Field(ge=0.0, le=1.0)
    
    @validator('x2')
    def x2_must_be_greater_than_x1(cls, v, values):
        if 'x1' in values and v <= values['x1']:
            raise ValueError('x2 must be greater than x1')
        return v
    
    @validator('y2')
    def y2_must_be_greater_than_y1(cls, v, values):
        if 'y1' in values and v <= values['y1']:
            raise ValueError('y2 must be greater than y1')
        return v

class DetectionCreateDTO(BaseModel):
    """DTO for creating a detection record"""
    image_url: Optional[str] = None
    model_version: str = Field(default="v1.0")
    confidence_threshold: float = Field(default=0.4, ge=0.0, le=1.0)
    detections: List[BoundingBoxDTO]

# ----- OUTPUT DTOs (What we return to client) -----

class DetectionResponseDTO(BaseModel):
    """DTO for returning detection with metrics"""
    id: int
    image_url: Optional[str]
    model_version: str
    status: DetectionStatus
    total_detections: int
    avg_confidence: float
    created_at: datetime
    
    # Performance metrics (from related table)
    inference_time_ms: Optional[float] = None
    preprocessing_time_ms: Optional[float] = None
    
    class Config:
        from_attributes = True  # Allows SQLAlchemy model -> Pydantic

class MetricsSummaryDTO(BaseModel):
    """DTO for metrics summary"""
    total_detections: int
    avg_confidence: float
    avg_inference_time: float
    detections_by_label: Dict[str, int]