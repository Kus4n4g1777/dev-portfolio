"""
Production Detection Persistence Service
- PostgreSQL for structured data (source of truth)
- Kafka for event streaming (decoupled consumers)
- Redis for caching (optional - dashboard performance)
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DetectionPersistenceService:
    """
    Handle detection storage across multiple systems
    """
    
    def __init__(self):
        # Main DB connection (dashboard_db)
        main_db_url = os.getenv(
            "MAIN_DB_URL",
            "postgresql://kus4n4g1:B3Str0ng@dashboard_db:5432/portfolio_db"
        )
        
        self.engine = create_engine(main_db_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # TODO: Add Kafka producer initialization
        # self.kafka_producer = KafkaProducer(...)
        
        # TODO: Add Redis client initialization  
        # self.redis_client = redis.Redis(...)
        
        logger.info("✅ Detection Persistence Service initialized")
    
    def _calculate_avg_confidence(self, detections: List[Dict]) -> float:
        """Calculate average confidence from detections"""
        if not detections:
            return 0.0
        
        confidences = [d.get('confidence', 0) for d in detections]
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _create_summary(self, detection_result: Dict) -> Dict:
        """Create lightweight summary for caching"""
        detections = detection_result.get('detections', [])
        
        # Count objects by label
        object_counts = {}
        for det in detections:
            label = det.get('label', 'unknown')
            object_counts[label] = object_counts.get(label, 0) + 1
        
        return {
            'total_objects': len(detections),
            'object_counts': object_counts,
            'avg_confidence': self._calculate_avg_confidence(detections),
            'has_llm_descriptions': bool(detection_result.get('llm_descriptions'))
        }
    
    async def save_detection(
        self, 
        detection_result: Dict,
        user_id: Optional[str] = None,
        processing_time_ms: Optional[float] = None
    ) -> str:
        """
        Save detection with proper persistence strategy
        
        Args:
            detection_result: Full detection output from YOLO + LLM
            user_id: Optional user identifier
            processing_time_ms: Time taken to process detection
        
        Returns:
            detection_id (UUID string)
        """
        detection_id = str(uuid.uuid4())
        
        session = self.SessionLocal()
        
        try:
            # 1. PERSIST to main DB (source of truth)
            query = text("""
                INSERT INTO detections 
                (id, user_id, image_url, detections_json, 
                 llm_descriptions, confidence_avg, processing_time_ms)
                VALUES (:id, :user_id, :image_url, :detections, 
                        :descriptions, :confidence, :processing_time)
                RETURNING id
            """)
            
            result = session.execute(query, {
                "id": detection_id,
                "user_id": user_id or "anonymous",
                "image_url": detection_result.get('image_url'),
                "detections": json.dumps(detection_result.get('detections', [])),
                "descriptions": json.dumps(detection_result.get('llm_descriptions', [])),
                "confidence": self._calculate_avg_confidence(
                    detection_result.get('detections', [])
                ),
                "processing_time": processing_time_ms
            })
            
            session.commit()
            
            logger.info(f"✅ Saved detection {detection_id} to PostgreSQL")
            
            # 2. TODO: PUBLISH to Kafka (for downstream consumers)
            # await self._publish_to_kafka(detection_id, detection_result, user_id)
            
            # 3. TODO: CACHE recent detections (optional, for dashboards)
            # await self._cache_detection(detection_id, detection_result, user_id)
            
            return detection_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving detection: {e}")
            raise
        finally:
            session.close()
    
    async def get_detection_by_id(self, detection_id: str) -> Optional[Dict]:
        """Retrieve single detection by ID"""
        session = self.SessionLocal()
        
        try:
            query = text("""
                SELECT id, timestamp, user_id, image_url, 
                       detections_json, llm_descriptions, 
                       confidence_avg, processing_time_ms, created_at
                FROM detections
                WHERE id = :detection_id
            """)
            
            result = session.execute(query, {"detection_id": detection_id})
            row = result.fetchone()
            
            if not row:
                return None
            
            return {
                'id': str(row.id),
                'timestamp': row.timestamp.isoformat(),
                'user_id': row.user_id,
                'image_url': row.image_url,
                'detections': json.loads(row.detections_json) if row.detections_json else [],
                'llm_descriptions': json.loads(row.llm_descriptions) if row.llm_descriptions else [],
                'confidence_avg': float(row.confidence_avg) if row.confidence_avg else 0.0,
                'processing_time_ms': float(row.processing_time_ms) if row.processing_time_ms else 0.0,
                'created_at': row.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching detection: {e}")
            return None
        finally:
            session.close()
    
    async def get_detection_history(
        self, 
        user_id: str, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Retrieve detection history for a user
        
        Returns list of detection summaries (not full data - performance!)
        """
        session = self.SessionLocal()
        
        try:
            query = text("""
                SELECT id, timestamp, user_id, confidence_avg, 
                       processing_time_ms,
                       jsonb_array_length(detections_json) as object_count
                FROM detections
                WHERE user_id = :user_id
                ORDER BY timestamp DESC
                LIMIT :limit OFFSET :offset
            """)
            
            result = session.execute(query, {
                "user_id": user_id,
                "limit": limit,
                "offset": offset
            })
            
            detections = []
            for row in result:
                detections.append({
                    'id': str(row.id),
                    'timestamp': row.timestamp.isoformat(),
                    'user_id': row.user_id,
                    'object_count': row.object_count,
                    'confidence_avg': float(row.confidence_avg) if row.confidence_avg else 0.0,
                    'processing_time_ms': float(row.processing_time_ms) if row.processing_time_ms else 0.0
                })
            
            return detections
            
        except Exception as e:
            logger.error(f"Error fetching detection history: {e}")
            return []
        finally:
            session.close()
    
    async def get_stats(self) -> Dict:
        """Get detection statistics"""
        session = self.SessionLocal()
        
        try:
            # Total detections
            total_query = text("SELECT COUNT(*) FROM detections")
            total = session.execute(total_query).scalar()
            
            # Detections today
            today_query = text("""
                SELECT COUNT(*) FROM detections 
                WHERE timestamp >= CURRENT_DATE
            """)
            today = session.execute(today_query).scalar()
            
            # Average confidence
            avg_conf_query = text("SELECT AVG(confidence_avg) FROM detections")
            avg_confidence = session.execute(avg_conf_query).scalar()
            
            # Average processing time
            avg_time_query = text("SELECT AVG(processing_time_ms) FROM detections")
            avg_processing_time = session.execute(avg_time_query).scalar()
            
            return {
                'total_detections': total or 0,
                'detections_today': today or 0,
                'avg_confidence': float(avg_confidence) if avg_confidence else 0.0,
                'avg_processing_time_ms': float(avg_processing_time) if avg_processing_time else 0.0,
                'database': 'dashboard_db (PostgreSQL)'
            }
            
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            return {
                'error': str(e),
                'database': 'dashboard_db (PostgreSQL)'
            }
        finally:
            session.close()
