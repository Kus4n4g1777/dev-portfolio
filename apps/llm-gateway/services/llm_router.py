"""
LLM Router with TRUE Round-Robin + Smart Fallback
- Round-robin: Rotates through ALL LLMs in order (different personalities)
- Fallback: If one fails, try Ollama (local, fast, never fails)
"""
import logging
import os
from typing import Optional, Dict, Tuple

import google.generativeai as genai
import requests


logger = logging.getLogger(__name__)


class LLMRouter:
    """Routes LLM requests with round-robin and smart fallback"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        
        self.rotation = [
            "gemini-2.5-flash",
            "dart",
            "go",
            "ollama",
            "gemini-1.5-pro",
        ]
        
        self.current_index = 0
        self.calls_by_runtime = {runtime: 0 for runtime in self.rotation}
        self.failures_by_runtime = {runtime: 0 for runtime in self.rotation}
        self.fallbacks_to_ollama = 0
        
        logger.info("✅ LLM Router initialized - TRUE ROUND-ROBIN mode")
    
    def _call_gemini(self, model_name: str, prompt: str) -> Optional[str]:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini {model_name} failed: {str(e)[:100]}")
            return None
    
    def _call_dart(self, prompt: str) -> Optional[str]:
        try:
            response = requests.post(
                "http://dart-runtime:8080/generate",
                json={"prompt": prompt},
                timeout=10,
            )
            if response.status_code == 200:
                return response.json().get("response")
            return None
        except Exception as e:
            logger.warning(f"Dart runtime failed: {str(e)[:100]}")
            return None
    
    def _call_go(self, prompt: str) -> Optional[str]:
        try:
            response = requests.post(
                "http://go-runtime:8081/generate",
                json={"prompt": prompt},
                timeout=10,
            )
            if response.status_code == 200:
                return response.json().get("response")
            return None
        except Exception as e:
            logger.warning(f"Go runtime failed: {str(e)[:100]}")
            return None
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        try:
            response = requests.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=30,
            )
            if response.status_code == 200:
                return response.json().get("response")
            return None
        except Exception as e:
            logger.error(f"Ollama failed (should never happen!): {e}")
            return None
    
    def _try_runtime(self, runtime: str, prompt: str) -> Tuple[Optional[str], bool]:
        logger.info(f"🎯 Calling {runtime}...")
        
        if runtime == "gemini-2.5-flash":
            response = self._call_gemini("gemini-2.5-flash", prompt)
        elif runtime == "gemini-1.5-pro":
            response = self._call_gemini("gemini-1.5-pro", prompt)
        elif runtime == "dart":
            response = self._call_dart(prompt)
        elif runtime == "go":
            response = self._call_go(prompt)
        elif runtime == "ollama":
            response = self._call_ollama(prompt)
        else:
            response = None
        
        success = response is not None
        
        if success:
            logger.info(f"✅ {runtime} succeeded")
            self.calls_by_runtime[runtime] += 1
        else:
            logger.warning(f"❌ {runtime} failed")
            self.failures_by_runtime[runtime] += 1
        
        return response, success
    
    def call_with_round_robin(self, prompt: str) -> Dict:
        """
        TRUE Round-Robin with smart fallback

        Flow:
        1. Try next runtime in rotation
        2. If it fails and it's not Ollama, fallback to Ollama immediately
        3. Move to next in rotation for the next call
        """
        primary_runtime = self.rotation[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.rotation)
        
        response, success = self._try_runtime(primary_runtime, prompt)
        
        if success:
            return {
                "response": response,
                "runtime": primary_runtime,
                "used_fallback": False,
                "success": True,
            }
        
        if primary_runtime != "ollama":
            logger.warning(f"⚠️ {primary_runtime} failed, falling back to Ollama...")
            self.fallbacks_to_ollama += 1
            
            response, success = self._try_runtime("ollama", prompt)
            
            if success:
                return {
                    "response": response,
                    "runtime": "ollama (fallback)",
                    "used_fallback": True,
                    "primary_tried": primary_runtime,
                    "success": True,
                }
        
        logger.error("❌ COMPLETE FAILURE - even Ollama failed!")
        return {
            "response": "Error: All models failed 😅",
            "runtime": "none",
            "used_fallback": True,
            "success": False,
        }
    
    def get_stats(self) -> Dict:
        return {
            "calls_by_runtime": self.calls_by_runtime,
            "failures_by_runtime": self.failures_by_runtime,
            "total_calls": sum(self.calls_by_runtime.values()),
            "fallbacks_to_ollama": self.fallbacks_to_ollama,
            "current_rotation_index": self.current_index,
            "next_runtime": self.rotation[self.current_index],
        }