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
    
    if request.runtime in ["ollama", "all"]:
        results["ollama"] = await generate_ollama(request.prompt)

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

async def generate_ollama(prompt: str) -> dict:
    """Generate using Ollama (local LLM)"""
    try:
        import ollama
        client = ollama.Client(host='http://ollama:11434')
        response = client.chat(
            model='llama3.2',
            messages=[{'role': 'user', 'content': prompt}]
        )
        return {
            "runtime": "ollama-local",
            "model": "llama3.2",
            "response": response['message']['content'],
            "error": None
        }
    except Exception as e:
        logger.error(f"Ollama error: {str(e)}")
        return {
            "runtime": "ollama-local",
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
    
    # Go
    start = time.time()
    results["go"] = await generate_go(request.prompt)
    results["go"]["latency_ms"] = (time.time() - start) * 1000
    
    # Ollama
    start = time.time()
    results["ollama"] = await generate_ollama(request.prompt)
    results["ollama"]["latency_ms"] = (time.time() - start) * 1000


    return {
        "prompt": request.prompt,
        "comparison": results
    }

# Polyglot RAG Service (separate vector DB)
from services.rag_service import RAGService
from pydantic import BaseModel

# Request models
class AddDocumentRequest(BaseModel):
    content: str
    source: str = "user"
    metadata: dict = None

class AskRAGRequest(BaseModel):
    question: str
    top_k: int = 5

# Lazy initialization - only create when first used
_rag_polyglot = None

def get_rag_service():
    global _rag_polyglot
    if _rag_polyglot is None:
        _rag_polyglot = RAGService()
    return _rag_polyglot

@app.post("/rag/documents/add")
async def add_rag_document(request: AddDocumentRequest):
    """Add document to RAG (vector DB)"""
    rag = get_rag_service()
    result = await rag.add_document(request.content, request.source, request.metadata)
    return result

@app.post("/rag/ask")
async def ask_rag_polyglot(request: AskRAGRequest):
    """RAG Query with Polyglot Architecture"""
    rag = get_rag_service()
    result = await rag.ask(request.question, request.top_k)
    return result

@app.get("/rag/stats")
async def rag_stats():
    """RAG system statistics from vector DB"""
    from sqlalchemy import text
    
    rag = get_rag_service()
    session = rag.SessionLocal()
    try:
        doc_count = session.execute(text("SELECT COUNT(*) FROM rag_documents")).scalar()
        query_count = session.execute(text("SELECT COUNT(*) FROM rag_query_logs")).scalar()
        
        return {
            "database": "vector_db (polyglot architecture)",
            "documents": doc_count,
            "queries": query_count
        }
    finally:
        session.close()

# ===================================================================
# DETECTION PERSISTENCE SERVICE
# ===================================================================
from services.detection_persistence import DetectionPersistenceService

# Lazy initialization
_detection_persistence = None

def get_detection_service():
    global _detection_persistence
    if _detection_persistence is None:
        _detection_persistence = DetectionPersistenceService()
    return _detection_persistence

@app.post("/detections/save")
async def save_detection(
    detection_result: dict,
    user_id: str = "anonymous",
    processing_time_ms: float = 0.0
):
    """
    Save detection result to PostgreSQL
    
    Expected format:
    {
        "detections": [...],
        "llm_descriptions": [...],
        "image_url": "..."
    }
    """
    service = get_detection_service()
    detection_id = await service.save_detection(
        detection_result,
        user_id=user_id,
        processing_time_ms=processing_time_ms
    )
    
    return {
        "status": "success",
        "detection_id": detection_id,
        "message": "Detection saved to PostgreSQL"
    }

@app.get("/detections/{detection_id}")
async def get_detection(detection_id: str):
    """Get detection by ID"""
    service = get_detection_service()
    detection = await service.get_detection_by_id(detection_id)
    
    if not detection:
        return {"error": "Detection not found"}
    
    return detection

@app.get("/detections/history/{user_id}")
async def get_detection_history(user_id: str, limit: int = 50, offset: int = 0):
    """Get detection history for user"""
    service = get_detection_service()
    history = await service.get_detection_history(user_id, limit, offset)
    
    return {
        "user_id": user_id,
        "total": len(history),
        "detections": history
    }

@app.get("/detections/stats")
async def get_detection_stats():
    """Get detection statistics"""
    service = get_detection_service()
    stats = await service.get_stats()
    return stats

# ===================================================================
# DETECTION BUFFER SERVICE (Real-time with LRU Cache)
# ===================================================================
from services.detection_buffer import DetectionBufferService

_detection_buffer = None

def get_buffer_service():
    global _detection_buffer
    if _detection_buffer is None:
        _detection_buffer = DetectionBufferService(buffer_size=4, cache_capacity=20)
    return _detection_buffer

class DetectionRequest(BaseModel):
    detection: dict

@app.post("/buffer/add-detection")
async def add_detection_to_buffer(request: DetectionRequest):
    """
    Add detection to buffer
    Returns AI response when buffer is full (or cached instantly)
    """
    try:
        service = get_buffer_service()
        result = service.add_detection(request.detection)  # ← FIX: request.detection
        
        if result:
            return result
        else:
            return {
                "status": "buffered",
                "buffer_count": len(service.buffer),
                "buffer_size": service.buffer_size,
                "message": f"Detection buffered ({len(service.buffer)}/{service.buffer_size})"
            }
    except Exception as e:
        import logging
        logging.error(f"Error in add_detection_to_buffer: {e}")
        raise

@app.get("/buffer/stats")
async def get_buffer_stats():
    """Get detection buffer statistics"""
    service = get_buffer_service()
    return service.get_stats()

@app.post("/buffer/clear")
async def clear_buffer():
    """Clear buffer without processing"""
    service = get_buffer_service()
    cleared = service.clear_buffer()
    return {"status": "cleared", "detections_discarded": cleared}
