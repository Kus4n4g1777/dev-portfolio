from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import time

from app.database import get_db
from app.models import DetectionResult, DetectionMetrics, BoundingBox, DetectionStatus
from app.schemas import (
    DetectionCreateDTO, 
    DetectionResponseDTO, 
    MetricsSummaryDTO
)

router = APIRouter(prefix="/detections", tags=["detections"])

# ===================================================================
# POST /api/detections - Create new detection record
# ===================================================================
@router.post("/", response_model=DetectionResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_detection(
    detection_data: DetectionCreateDTO,
    db: Session = Depends(get_db)
):
    """
    Create a new detection record with metrics.
    
    THIS IS THE CORE PATTERN:
    1. Receive validated DTO ✅
    2. Start transaction
    3. Create parent record
    4. Flush to get ID
    5. Create related records (metrics, bounding boxes)
    6. Commit
    7. Return response DTO
    """
    # Simulate timing (in real app, this comes from actual detection)
    start_time = time.time()
    
    # Calculate metrics from input
    total_detections = len(detection_data.detections)
    avg_confidence = (
        sum(d.confidence for d in detection_data.detections) / total_detections
        if total_detections > 0 else 0.0
    )
    
    try:
        # Create parent detection record
        db_detection = DetectionResult(
            image_url=detection_data.image_url,
            model_version=detection_data.model_version,
            status=DetectionStatus.COMPLETED,
            total_detections=total_detections,
            avg_confidence=avg_confidence
        )
        db.add(db_detection)
        db.flush()  # Get the ID without committing yet ← IMPORTANT!
        
        # Create metrics record (one-to-one relationship)
        inference_time = (time.time() - start_time) * 1000
        db_metrics = DetectionMetrics(
            detection_id=db_detection.id,
            inference_time_ms=inference_time,
            preprocessing_time_ms=10.5,  # Mock value
            postprocessing_time_ms=5.2,  # Mock value
            total_time_ms=inference_time + 15.7
        )
        db.add(db_metrics)
        
        # Create bounding box records (one-to-many relationship)
        for bbox_data in detection_data.detections:
            db_bbox = BoundingBox(
                detection_id=db_detection.id,
                x1=bbox_data.x1,
                y1=bbox_data.y1,
                x2=bbox_data.x2,
                y2=bbox_data.y2,
                label=bbox_data.label,
                confidence=bbox_data.confidence
            )
            db.add(db_bbox)
        
        # Commit transaction (all or nothing)
        db.commit()
        db.refresh(db_detection)
        
        # Return response DTO
        return DetectionResponseDTO(
            id=db_detection.id,
            image_url=db_detection.image_url,
            model_version=db_detection.model_version,
            status=db_detection.status,
            total_detections=db_detection.total_detections,
            avg_confidence=db_detection.avg_confidence,
            created_at=db_detection.created_at,
            inference_time_ms=db_metrics.inference_time_ms,
            preprocessing_time_ms=db_metrics.preprocessing_time_ms
        )
        
    except Exception as e:
        db.rollback()  # Rollback on error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


# ===================================================================
# GET /api/detections/{detection_id} - Get single detection
# ===================================================================
@router.get("/{detection_id}", response_model=DetectionResponseDTO)
async def get_detection(detection_id: int, db: Session = Depends(get_db)):
    """Get a single detection by ID"""
    
    detection = (
        db.query(DetectionResult)
        .filter(DetectionResult.id == detection_id)
        .first()
    )
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection with id {detection_id} not found"
        )
    
    return detection


# ===================================================================
# GET /api/detections - List all detections (with pagination)
# ===================================================================
@router.get("/", response_model=List[DetectionResponseDTO])
async def list_detections(
    skip: int = 0,
    limit: int = 10,
    model_version: str = None,
    db: Session = Depends(get_db)
):
    """
    List detections with optional filtering.
    
    Demonstrates:
    - Pagination (skip/limit)
    - Optional filters
    - Query optimization
    """
    
    query = db.query(DetectionResult)
    
    # Apply filter if provided
    if model_version:
        query = query.filter(DetectionResult.model_version == model_version)
    
    # Pagination
    detections = query.offset(skip).limit(limit).all()
    
    return detections


# ===================================================================
# GET /api/detections/metrics/summary - Aggregated metrics
# ===================================================================
@router.get("/metrics/summary", response_model=MetricsSummaryDTO)
async def get_metrics_summary(db: Session = Depends(get_db)):
    """
    Get aggregated metrics across all detections.
    
    Demonstrates:
    - SQL aggregations (SUM, AVG, COUNT)
    - GROUP BY queries
    - Multiple table joins
    """
    
    # Get overall stats
    stats = db.query(
        func.sum(DetectionResult.total_detections).label('total'),
        func.avg(DetectionResult.avg_confidence).label('avg_conf')
    ).first()
    
    # Get average inference time from metrics table
    avg_time = db.query(
        func.avg(DetectionMetrics.inference_time_ms)
    ).scalar()
    
    # Get detection counts by label (GROUP BY)
    label_counts = (
        db.query(BoundingBox.label, func.count(BoundingBox.id))
        .group_by(BoundingBox.label)
        .all()
    )
    
    return MetricsSummaryDTO(
        total_detections=stats.total or 0,
        avg_confidence=float(stats.avg_conf or 0.0),
        avg_inference_time=float(avg_time or 0.0),
        detections_by_label={label: count for label, count in label_counts}
    )


# ===================================================================
# DELETE /api/detections/{detection_id} - Delete detection
# ===================================================================
@router.delete("/{detection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_detection(detection_id: int, db: Session = Depends(get_db)):
    """
    Delete a detection and cascade to related records.
    
    Demonstrates:
    - CASCADE deletes (defined in foreign key)
    - Transaction safety
    """
    
    detection = (
        db.query(DetectionResult)
        .filter(DetectionResult.id == detection_id)
        .first()
    )
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection with id {detection_id} not found"
        )
    
    db.delete(detection)
    db.commit()
    
    return None