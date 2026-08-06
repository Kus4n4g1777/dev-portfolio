"""
Detection Buffer Service with AI Response Generation
- Buffers detections (batch processing)
- Generates adaptive prompts based on confidence
- Integrates with LRU Cache for response caching
"""
import time
import logging
import locale
import os
from typing import Dict, List, Optional

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
    
        self.llm_router = LLMRouter()
        
        self.total_detections = 0
        self.ai_calls = 0
        self.cached_responses = 0
        
        self.confidence_distribution = {
            "excellent": 0,
            "good": 0,
            "moderate": 0,
            "acceptable": 0,
            "threshold": 0,
            "rejected": 0,
        }
        
        self.latencies = {
            "cache_hit": [],
            "llm_call": [],
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
        
        confidences = [d.get("confidence", 0) for d in detections]
        return sum(confidences) / len(confidences)

    def _get_response_language(self) -> str:
        """
        Language selection strategy:
        1. APP_LANGUAGE=en|es overrides everything
        2. AUTO_DETECT_LANGUAGE=true enables OS locale detection
        3. Default fallback is English
        """
        forced_language = os.getenv("APP_LANGUAGE", "").strip().lower()
        if forced_language in {"en", "es"}:
            return forced_language

        auto_detect = os.getenv("AUTO_DETECT_LANGUAGE", "false").strip().lower() == "true"
        if not auto_detect:
            return "en"

        env_locale = (
            os.getenv("LC_ALL")
            or os.getenv("LC_MESSAGES")
            or os.getenv("LANG")
            or ""
        ).lower()

        if env_locale.startswith("es"):
            return "es"
        if env_locale.startswith("en"):
            return "en"

        try:
            system_locale = locale.getlocale()[0]
            if system_locale:
                system_locale = system_locale.lower()
                if system_locale.startswith("es"):
                    return "es"
                if system_locale.startswith("en"):
                    return "en"
        except Exception as e:
            logger.warning(f"Could not detect OS locale: {str(e)[:100]}")

        return "en"

    def _generate_adaptive_prompt(self, avg_confidence: float, detection_count: int) -> str:
        """
        Generate prompt based on confidence level with humor/irony
        """
        language = self._get_response_language()

        if language == "es":
            if avg_confidence >= 0.90:
                return f"""I have {detection_count} heart detections with {avg_confidence*100:.1f}% confidence.

Respond in Spanish, using MAXIMUM 2 lines, with a cheerful and confident tone.
Example: "¡Perfecto! Esos corazones están clarísimos. Detección impecable 💪❤"
"""
            elif avg_confidence >= 0.75:
                return f"""I have {detection_count} heart detections with {avg_confidence*100:.1f}% confidence.

Respond in Spanish, using MAXIMUM 2 lines, with a positive tone and a bit of humor.
Example: "¡Muy bien! Corazones detectados con confianza. Tu pulso está tranquilo 😊❤"
"""
            elif avg_confidence >= 0.60:
                return f"""I have {detection_count} heart detections with {avg_confidence*100:.1f}% confidence.

Respond in Spanish, using MAXIMUM 2 lines, with a lightly playful tone.
Example: "¡Ahí vamos! Corazones detectados. ¿Un poco nervioso quizás? 😅❤"
"""
            elif avg_confidence >= 0.45:
                return f"""I have {detection_count} heart detections with {avg_confidence*100:.1f}% confidence.

Respond in Spanish, using MAXIMUM 2 lines, with a playful/ironic tone.
Example: "Hmm... creo que veo corazones... o tal vez no. ¿Mano temblorosa? 🤔❤"
"""
            elif avg_confidence >= 0.40:
                return f"""I have {detection_count} heart detections with {avg_confidence*100:.1f}% confidence (right at the detection threshold).

Respond in Spanish, using MAXIMUM 2 lines, with a very ironic and funny tone.
Example: "¿Eso es un corazón o una mancha? Estamos en el límite aquí... 😂💔"
"""
            else:
                return f"""I have {detection_count} detection attempts with {avg_confidence*100:.1f}% confidence (below the 40% threshold).

Respond in Spanish, using MAXIMUM 2 lines, with a very playful tone about the REJECTION.
Example: "Eso NO son corazones, amigo. ¿Café derramado? ¿Manchas de tinta? 😂❌"
"""

        if avg_confidence >= 0.90:
            return f"""I have {detection_count} heart detections with {avg_confidence*100:.1f}% confidence.

Respond in English, using MAXIMUM 2 lines, with a cheerful and confident tone.
Example: "Perfect! Those hearts are crystal clear. Flawless detection 💪❤"
"""
        elif avg_confidence >= 0.75:
            return f"""I have {detection_count} heart detections with {avg_confidence*100:.1f}% confidence.

Respond in English, using MAXIMUM 2 lines, with a positive tone and a bit of humor.
Example: "Nice! Hearts detected with confidence. Your pulse looks pretty calm 😊❤"
"""
        elif avg_confidence >= 0.60:
            return f"""I have {detection_count} heart detections with {avg_confidence*100:.1f}% confidence.

Respond in English, using MAXIMUM 2 lines, with a lightly playful tone.
Example: "We’re getting there! Hearts detected. A little nervous maybe? 😅❤"
"""
        elif avg_confidence >= 0.45:
            return f"""I have {detection_count} heart detections with {avg_confidence*100:.1f}% confidence.

Respond in English, using MAXIMUM 2 lines, with a playful/ironic tone.
Example: "Hmm... I think I see hearts... or maybe not. Shaky hands? 🤔❤"
"""
        elif avg_confidence >= 0.40:
            return f"""I have {detection_count} heart detections with {avg_confidence*100:.1f}% confidence (right at the detection threshold).

Respond in English, using MAXIMUM 2 lines, with a very ironic and funny tone.
Example: "Is that a heart or a smudge? We’re really pushing the limit here... 😂💔"
"""
        else:
            return f"""I have {detection_count} detection attempts with {avg_confidence*100:.1f}% confidence (below the 40% threshold).

Respond in English, using MAXIMUM 2 lines, with a very playful tone about the REJECTION.
Example: "Those are definitely NOT hearts, my friend. Spilled coffee? Ink stains? 😂❌"
"""
    
    def _call_llm_with_fallback(self, prompt: str) -> tuple[str, str]:
        """
        Call LLM with round-robin + fallback
        Returns: (response, runtime_used)
        """
        logger.info("🎯 Calling LLM Router...")

        result = self.llm_router.call_with_round_robin(prompt)
        
        logger.info(
            f"📊 Router result: runtime={result.get('runtime')}, "
            f"success={result.get('success')}, "
            f"fallback={result.get('used_fallback', False)}"
        )

        if result["success"]:
            self.ai_calls += 1
            return result["response"], result["runtime"]

        return "Error: All models failed 😅", "none"
    
    def _judge_response(
        self, response: str, avg_confidence: float, detection_count: int
    ) -> dict:
        """
        LLM-as-a-Judge — evaluates the quality of a generated AI response
        before it leaves the gateway.
        """
        judge_prompt = f"""You are an AI response quality judge. Evaluate this response strictly.
CONTEXT:
- A YOLOv8 model processed {detection_count} detections
- Average confidence: {avg_confidence * 100:.1f}%
- The response should be max 2 lines, with humor/irony proportional to confidence

RESPONSE TO EVALUATE:
"{response}"

Score each criterion from 1 to 10:
1. RELEVANCE: Does the response address the detection result meaningfully?
2. TONE: Is the humor/irony level appropriate for {avg_confidence * 100:.1f}% confidence?
3. CONCISENESS: Is it 2 lines or fewer?

Reply ONLY with this JSON format, nothing else:
{{"relevance": <1-10>, "tone": <1-10>, "conciseness": <1-10>, "reason": "<one sentence>"}}
"""
        try:
            import google.generativeai as genai
            import json
            
            # We use the Gemini API key (we ensure GEMINI_API_KEY is in our .env)
            model = genai.GenerativeModel("gemini-2.5-flash")
            result = model.generate_content(judge_prompt)
            
            # We clean up potential markdown formatting from the JSON output (```json ... ```)
            raw = result.text.strip()
            if raw.startswith("```"):
                raw = "\n".join(raw.split("\n")[1:-1])
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
                
            scores = json.loads(raw)
            overall = round(
                (scores["relevance"] + scores["tone"] + scores["conciseness"]) / 3, 2
            )
            
            logger.info(
                f"⚖️  Judge scores → relevance={scores['relevance']} "
                f"tone={scores['tone']} conciseness={scores['conciseness']} "
                f"overall={overall} | {scores.get('reason', '')}"
            )
            
            return {
                "relevance": scores["relevance"],
                "tone": scores["tone"],
                "conciseness": scores["conciseness"],
                "overall": overall,
                "approved": overall >= 7.0,
                "reason": scores.get("reason", ""),
            }
        except Exception as e:
            logger.warning(f"⚖️  Judge failed (non-fatal): {e}")
            # If the judge fails due to rate limits or network issues, we approve by default 
            # so we don't take down the gateway
            return {
                "relevance": 0, "tone": 0, "conciseness": 0,
                "overall": 10.0, "approved": True, "reason": f"Judge unavailable: {e}"
            }
    def _process_buffer(self) -> Dict:
        if not self.buffer:
            return None
        
        avg_confidence = self._calculate_avg_confidence(self.buffer)
        detection_count = len(self.buffer)
        
        bucket = self.cache._get_confidence_bucket(avg_confidence)
        self.confidence_distribution[bucket] += 1
        
        start_time = time.time()
        cached_response = self.cache.get(avg_confidence)
        
        if cached_response:
            self.cached_responses += 1
            latency_ms = (time.time() - start_time) * 1000
            self.latencies["cache_hit"].append(latency_ms)
            
            processed_buffer = self.buffer.copy()
            self.buffer = []
            
            logger.info(f"⚡ Cache HIT | latency: {latency_ms:.2f}ms")

            return {
                "source": "cache",
                "response": cached_response,
                "runtime": "cache",
                "cache_hit": True,
                "avg_confidence": avg_confidence,
                "confidence_bucket": bucket,
                "detection_count": detection_count,
                "detections": processed_buffer,
                "latency_ms": latency_ms,
            }
        
        logger.info("⏳ Cache miss - calling LLM...")
        
        prompt = self._generate_adaptive_prompt(avg_confidence, detection_count)
        ai_response, runtime_used = self._call_llm_with_fallback(prompt)
        
        latency_ms = (time.time() - start_time) * 1000
        self.latencies["llm_call"].append(latency_ms)
        
        # --- NEW: LLM-as-a-Judge Step ---
        # We evaluate the response that just came out of the LLM Router
        judge_result = self._judge_response(ai_response, avg_confidence, detection_count)
        
        if not judge_result["approved"]:
            logger.warning(f"🚫 Judge rejected response (score: {judge_result['overall']}). Using fallback.")
            ai_response = f"Fallback: Response rejected by AI Judge due to low quality 😅 (Reason: {judge_result['reason']})"
        else:
            # We only cache the response if it passed the judge's audit (>= 7.0)
            self.cache.put(avg_confidence, ai_response) 
        
        processed_buffer = self.buffer.copy() 
        self.buffer = [] 
        
        return { 
            "source": "llm", 
            "response": ai_response, 
            "runtime": runtime_used, 
            "cache_hit": False, 
            "avg_confidence": avg_confidence, 
            "confidence_bucket": bucket, 
            "detection_count": detection_count, 
            "detections": processed_buffer, 
            "latency_ms": latency_ms, 
            # --- We add the Judge's evidence to the payload ---
            "judge_score": judge_result.get("overall"),
            "judge_reason": judge_result.get("reason"),
        }
    
    def get_stats(self) -> Dict:
        """Get comprehensive service statistics"""
        cache_stats = self.cache.get_stats()
        router_stats = self.llm_router.get_stats()

        avg_cache_latency = (
            sum(self.latencies["cache_hit"]) / len(self.latencies["cache_hit"])
            if self.latencies["cache_hit"] else 0
        )
        
        avg_llm_latency = (
            sum(self.latencies["llm_call"]) / len(self.latencies["llm_call"])
            if self.latencies["llm_call"] else 0
        )
        
        return {
            "buffer": {
                "size": self.buffer_size,
                "current_detections": len(self.buffer),
                "total_detections_processed": self.total_detections,
            },
            "confidence_distribution": self.confidence_distribution,
            "detection_threshold": 0.4,
            "critical_zone_detections": self.confidence_distribution["threshold"],
            "ai": {
                "total_calls": self.ai_calls,
                "cached_responses": self.cached_responses,
                "cache_hit_rate": cache_stats["hit_rate_percentage"],
            },
            "llm_router": router_stats,
            "latency": {
                "avg_cache_hit_ms": round(avg_cache_latency, 2),
                "avg_llm_call_ms": round(avg_llm_latency, 2),
                "speedup_factor": round(avg_llm_latency / avg_cache_latency, 2) if avg_cache_latency > 0 else 0,
            },
            "cache": cache_stats,
        }
    
    def clear_buffer(self):
        """Clear current buffer AND cache AND stats for clean test isolation"""
        cleared_count = len(self.buffer)
        self.buffer = []
        # Reset LRU cache completely
        self.cache = LRUCache(capacity=self.cache.capacity)
        # Reset all stats counters
        self.total_detections = 0
        self.ai_calls = 0
        self.cached_responses = 0
        self.confidence_distribution = {k: 0 for k in self.confidence_distribution}
        self.latencies = {"cache_hit": [], "llm_call": []}
        return cleared_count
