from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Gateway", version="1.0.0")

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')  # ← FIXED
else:
    gemini_model = None
    logger.warning("GEMINI_API_KEY not set")

# Service URLs
DART_SERVICE_URL = os.getenv("DART_SERVICE_URL", "http://dart-runtime:8080")
GO_SERVICE_URL = os.getenv("GO_SERVICE_URL", "http://go-runtime:8081")

class PromptRequest(BaseModel):
    prompt: str
    runtime: str = "python"  # python, dart, go, all

class DetectionRequest(BaseModel):
    object: str
    confidence: float

@app.get("/")
async def root():
    return {
        "service": "LLM Gateway",
        "version": "1.0.0",
        "runtimes": ["python", "dart", "go"]
    }

@app.get("/health")
async def health():
    services_status = {
        "python": "healthy",
        "dart": "unknown",
        "go": "unknown"
    }
    
    # Check Dart service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DART_SERVICE_URL}/health", timeout=2.0)
            services_status["dart"] = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        services_status["dart"] = "unreachable"
    
    # Check Go service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{GO_SERVICE_URL}/health", timeout=2.0)
            services_status["go"] = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        services_status["go"] = "unreachable"
    
    return {"status": "healthy", "services": services_status}

@app.post("/generate")
async def generate(request: PromptRequest):
    """Route request to specified runtime(s)"""
    
    results = {}
    
    if request.runtime in ["python", "all"]:
        results["python"] = await generate_python(request.prompt)
    
    if request.runtime in ["dart", "all"]:
        results["dart"] = await generate_dart(request.prompt)
    
    if request.runtime in ["go", "all"]:
        results["go"] = await generate_go(request.prompt)
    
    return {
        "prompt": request.prompt,
        "runtime": request.runtime,
        "results": results
    }

async def generate_python(prompt: str) -> dict:
    """Generate using Gemini via Python runtime"""
    if not gemini_model:
        return {"error": "Gemini API key not configured", "runtime": "python"}
    
    try:
        response = gemini_model.generate_content(prompt)
        return {
            "runtime": "python",
            "model": "gemini-2.5-flash",
            "response": response.text,
            "error": None
        }
    except Exception as e:
        logger.error(f"Python runtime error: {str(e)}")
        return {
            "runtime": "python",
            "error": str(e),
            "response": None
        }

async def generate_dart(prompt: str) -> dict:
    """Forward request to Dart runtime service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DART_SERVICE_URL}/generate",
                json={"prompt": prompt},
                timeout=30.0
            )
            return response.json()
    except Exception as e:
        logger.error(f"Dart runtime error: {str(e)}")
        return {
            "runtime": "dart",
            "error": str(e),
            "response": None
        }

async def generate_go(prompt: str) -> dict:
    """Forward request to Go runtime service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GO_SERVICE_URL}/generate",
                json={"prompt": prompt},
                timeout=30.0
            )
            return response.json()
    except Exception as e:
        logger.error(f"Go runtime error: {str(e)}")
        return {
            "runtime": "go",
            "error": str(e),
            "response": None
        }

@app.post("/describe-detection")
async def describe_detection(request: DetectionRequest):
    """Describe a detected object using best available runtime"""
    prompt = f"Describe what a {request.object} is in 2-3 sentences. Detection confidence: {request.confidence:.2%}"
    
    # Try Dart first (most relevant), fallback to Python
    dart_result = await generate_dart(prompt)
    if dart_result.get("error"):
        python_result = await generate_python(prompt)
        return {"primary": python_result, "fallback_used": True}
    
    return {"primary": dart_result, "fallback_used": False}

@app.post("/compare-runtimes")
async def compare_runtimes(request: PromptRequest):
    """Compare response from all runtimes"""
    import time
    
    results = {}
    
    # Python
    start = time.time()
    results["python"] = await generate_python(request.prompt)
    results["python"]["latency_ms"] = (time.time() - start) * 1000
    
    # Dart
    start = time.time()
    results["dart"] = await generate_dart(request.prompt)
    results["dart"]["latency_ms"] = (time.time() - start) * 1000
    
    # Go (optional)
    start = time.time()
    results["go"] = await generate_go(request.prompt)
    results["go"]["latency_ms"] = (time.time() - start) * 1000
    
    return {
        "prompt": request.prompt,
        "comparison": results
    }
