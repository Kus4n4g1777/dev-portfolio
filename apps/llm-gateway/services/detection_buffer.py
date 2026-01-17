"""
Detection Buffer Service with AI Response Generation
- Buffers detections (batch processing)
- Generates adaptive prompts based on confidence
- Integrates with LRU Cache for response caching
"""
import time
import logging
from typing import Dict, List, Optional
import google.generativeai as genai
import os

from .lru_cache import LRUCache
from .llm_router import LLMRouter

logger = logging.getLogger(__name__)

class DetectionBufferService:
    """
    Buffers detections and generates AI responses with caching
    """
    
    def __init__(self, buffer_size: int = 4, cache_capacity: int = 20):
        self.buffer_size = buffer_size
        self.buffer: List[Dict] = []
        self.cache = LRUCache(capacity=cache_capacity)
    
        # Use LLM Router for round-robin + fallback
        self.llm_router = LLMRouter()
        
        # Metrics
        self.total_detections = 0
        self.ai_calls = 0
        self.cached_responses = 0
        
        # Confidence distribution tracking
        self.confidence_distribution = {
            'excellent': 0,
            'good': 0,
            'moderate': 0,
            'acceptable': 0,
            'threshold': 0,
            'rejected': 0
        }
        
        # Latency tracking
        self.latencies = {
            'cache_hit': [],
            'gemini_call': []
        }
        
        logger.info(f"✅ Detection Buffer Service initialized (buffer_size={buffer_size})")
    
    def add_detection(self, detection: Dict) -> Optional[Dict]:
        """
        Add detection to buffer
        Returns AI response when buffer is full (or cached response immediately)
        """
        self.buffer.append(detection)
        self.total_detections += 1
        
        logger.info(f"📥 Detection added to buffer ({len(self.buffer)}/{self.buffer_size})")
        
        if len(self.buffer) >= self.buffer_size:
            return self._process_buffer()
        
        return None
    
    def _calculate_avg_confidence(self, detections: List[Dict]) -> float:
        """Calculate average confidence from buffer"""
        if not detections:
            return 0.0
        
        confidences = [d.get('confidence', 0) for d in detections]
        return sum(confidences) / len(confidences)
    
    def _generate_adaptive_prompt(self, avg_confidence: float, detection_count: int) -> str:
        """
        Generate prompt based on confidence level with humor/irony
        """
        if avg_confidence >= 0.90:
            return f"""Tengo {detection_count} detecciones de corazones con {avg_confidence*100:.1f}% de confianza.

Responde con MÁXIMO 2 líneas, tono alegre y seguro.
Ejemplo: "¡Perfecto! Esos corazones están clarísimos. Detección impecable 💪❤️"
"""
        
        elif avg_confidence >= 0.75:
            return f"""Tengo {detection_count} detecciones de corazones con {avg_confidence*100:.1f}% de confianza.

Responde con MÁXIMO 2 líneas, tono positivo con ligero humor.
Ejemplo: "¡Muy bien! Corazones detectados con confianza. Tu pulso está tranquilo 😊❤️"
"""
        
        elif avg_confidence >= 0.60:
            return f"""Tengo {detection_count} detecciones de corazones con {avg_confidence*100:.1f}% de confianza.

Responde con MÁXIMO 2 líneas, tono ligeramente bromista.
Ejemplo: "¡Ahí vamos! Corazones detectados. ¿Un poco nervioso quizás? 😅❤️"
"""
        
        elif avg_confidence >= 0.45:
            return f"""Tengo {detection_count} detecciones de corazones con {avg_confidence*100:.1f}% de confianza.

Responde con MÁXIMO 2 líneas, tono bromista/irónico.
Ejemplo: "Hmm... creo que veo corazones... o tal vez no. ¿Mano temblorosa? 🤔❤️"
"""
        
        elif avg_confidence >= 0.40:
            return f"""Tengo {detection_count} detecciones de corazones con {avg_confidence*100:.1f}% de confianza (justo en el límite de detección).

Responde con MÁXIMO 2 líneas, tono muy irónico y divertido.
Ejemplo: "¿Eso es un corazón o una mancha? Estamos en el límite aquí... 😂💔"
"""
        
        else:
            return f"""Tengo {detection_count} intentos de detección con {avg_confidence*100:.1f}% de confianza (por debajo del threshold de 40%).

Responde con MÁXIMO 2 líneas, tono muy bromista sobre el RECHAZO.
Ejemplo: "Eso NO son corazones, amigo. ¿Café derramado? ¿Manchas de tinta? 😂❌"
"""
    
    def _call_llm_with_fallback(self, prompt: str) -> tuple[str, str]:
        """
        Call LLM with round-robin + fallback
        Returns: (response, runtime_used)
        """
        import logging
        logger.info("🎯 Calling LLM Router...")

        result = self.llm_router.call_with_round_robin(prompt)
        
        logger.info(f"📊 Router result: runtime={result.get('runtime')}, success={result.get('success')}, fallback={result.get('used_fallback', False)}")

        if result['success']:
            self.ai_calls += 1
            return result['response'], result['runtime']
        else:
            # All runtimes failed
            return "Error: Todos los modelos fallaron 😅", "none"
    
    def _process_buffer(self) -> Dict:
        """
        Process buffered detections
        Returns response (cached or from AI)
        """
        if not self.buffer:
            return None
        
        avg_confidence = self._calculate_avg_confidence(self.buffer)
        detection_count = len(self.buffer)
        
        # Update confidence distribution
        bucket = self.cache._get_confidence_bucket(avg_confidence)
        self.confidence_distribution[bucket] += 1
        
        # Try cache FIRST
        start_time = time.time()
        cached_response = self.cache.get(avg_confidence)
        
        if cached_response:
            self.cached_responses += 1
            latency_ms = (time.time() - start_time) * 1000
            self.latencies['cache_hit'].append(latency_ms)
            
            processed_buffer = self.buffer.copy()
            self.buffer = []
            
            return {
                'source': 'cache',
                'response': cached_response,
                'runtime': 'cache',
                'avg_confidence': avg_confidence,
                'confidence_bucket': bucket,
                'detection_count': detection_count,
                'detections': processed_buffer,
                'latency_ms': latency_ms
            }
        
        # Cache miss - call AI
        logger.info("⏳ Cache miss - calling Gemini API...")
        
        prompt = self._generate_adaptive_prompt(avg_confidence, detection_count)
        
        # FIXED: Synchronous call (no async loop issues)
        ai_response, runtime_used = self._call_llm_with_fallback(prompt)
        
        latency_ms = (time.time() - start_time) * 1000
        self.latencies['gemini_call'].append(latency_ms)
        
        # Cache the response
        self.cache.put(avg_confidence, ai_response)
        
        processed_buffer = self.buffer.copy()
        self.buffer = []
        
        return {
            'source': 'gemini',  # ← Cambiar a 'llm'
            'response': ai_response,
            'runtime': runtime_used,  # ← NUEVO!
            'avg_confidence': avg_confidence,
            'confidence_bucket': bucket,
            'detection_count': detection_count,
            'detections': processed_buffer,
            'latency_ms': latency_ms
        }
    
    def get_stats(self) -> Dict:
        """Get comprehensive service statistics"""
        cache_stats = self.cache.get_stats()
        router_stats = self.llm_router.get_stats()

        avg_cache_latency = (
            sum(self.latencies['cache_hit']) / len(self.latencies['cache_hit'])
            if self.latencies['cache_hit'] else 0
        )
        
        avg_gemini_latency = (
            sum(self.latencies['gemini_call']) / len(self.latencies['gemini_call'])
            if self.latencies['gemini_call'] else 0
        )
        
        return {
            'buffer': {
                'size': self.buffer_size,
                'current_detections': len(self.buffer),
                'total_detections_processed': self.total_detections
            },
            'confidence_distribution': self.confidence_distribution,
            'detection_threshold': 0.4,
            'critical_zone_detections': self.confidence_distribution['threshold'],
            'ai': {
                'total_calls': self.ai_calls,
                'cached_responses': self.cached_responses,
                'cache_hit_rate': cache_stats['hit_rate_percentage']
            },
            'llm_router': router_stats,
            'latency': {
                'avg_cache_hit_ms': round(avg_cache_latency, 2),
                'avg_gemini_call_ms': round(avg_gemini_latency, 2),
                'speedup_factor': round(avg_gemini_latency / avg_cache_latency, 2) if avg_cache_latency > 0 else 0
            },
            'cache': cache_stats
        }
    
    def clear_buffer(self):
        """Clear current buffer without processing"""
        cleared_count = len(self.buffer)
        self.buffer = []
        return cleared_count
