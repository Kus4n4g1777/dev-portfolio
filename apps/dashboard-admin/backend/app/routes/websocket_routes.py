from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
import numpy as np
import cv2
import base64
import httpx
from detection_model.detector import detect  # TFLite detection function

router = APIRouter(
    prefix="/ws",
    tags=["websocket"]
)

active_connections: list[WebSocket] = []

# Configuration
BUFFER_SIZE = 4  # Send to LLM Gateway every 4 frames
LLM_GATEWAY_URL = "http://llm-gateway:8000/buffer/add-detection"
LLM_TIMEOUT = 5.0  # seconds

# ------------------------------
# Helper to decode base64 image
# ------------------------------
def decode_base64_image(data: str) -> np.ndarray:
    """
    Decode base64 string to OpenCV image
    
    Handles both raw base64 and data URI format
    (e.g., "data:image/jpeg;base64,...")
    """
    if "," in data:
        data = data.split(",")[1]
    img_bytes = base64.b64decode(data)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


# ------------------------------
# Helper to encode image to base64
# ------------------------------
def encode_base64_image(img: np.ndarray) -> str:
    """
    Encode OpenCV image to base64 data URI
    
    Returns format: "data:image/jpeg;base64,..."
    """
    _, buffer = cv2.imencode(".jpg", img)
    base64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_str}"


# ------------------------------
# Draw detection boxes
# ------------------------------
def draw_detections(img: np.ndarray, detections: list) -> np.ndarray:
    """
    Draw bounding boxes and labels on image
    
    Expected detection format:
    {
        "bbox": [x1, y1, x2, y2],  # normalized or pixel coords
        "label": "heart",
        "confidence": 0.95
    }
    """
    for det in detections:
        bbox = det.get("bbox", [])
        label = det.get("label", "object")
        conf = det.get("confidence", 0.0)
        
        if len(bbox) == 4:
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            text = f"{label} {conf:.2f}"
            cv2.putText(
                img, text, (x1, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
            )
    return img


# ------------------------------
# Call LLM Gateway for AI response
# ------------------------------
async def get_ai_response(detections: list) -> dict:
    """
    Send detections to LLM Gateway for AI-generated response
    
    Returns:
    {
        "response": "AI message text",
        "runtime": "gemini-2.5-flash",
        "source": "cache" or runtime name,
        "cache_hit": true/false
    }
    
    Returns None if LLM Gateway fails (graceful degradation)
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LLM_GATEWAY_URL,
                json={"detections": detections},
                timeout=LLM_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ AI response from {data.get('runtime', 'unknown')}")
                return {
                    "response": data.get("response", ""),
                    "runtime": data.get("runtime", "unknown"),
                    "source": data.get("source", "unknown"),
                    "cache_hit": data.get("source") == "cache"
                }
    except Exception as e:
        print(f"❌ LLM Gateway error: {e}")
    
    return None


# ------------------------------
# WebSocket endpoint for real-time detection
# ------------------------------
@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """
    WebSocket endpoint for real-time object detection with AI responses
    
    Flow:
    1. Receive base64 frame from Flutter
    2. Decode and run YOLO detection
    3. Send detections back to Flutter (every frame)
    4. Every 4 frames: send batch to LLM Gateway for AI response
    
    Why buffer 4 frames?
    - Reduces LLM calls (expensive)
    - Provides more context for AI
    - Leverages LRU cache effectively
    - Prevents message spam in UI
    
    Response format:
    {
        "detections": [...],           // Every frame
        "ai_response": "...",           // Every 4 frames (optional)
        "runtime": "gemini-2.5-flash",  // Every 4 frames (optional)
        "cache_hit": true/false         // Every 4 frames (optional)
    }
    """
    await websocket.accept()
    active_connections.append(websocket)
    print(f"✅ Client connected: {websocket.client.host}")
    
    # Initialize buffer for AI responses
    frame_count = 0
    detection_buffer = []
    
    try:
        while True:
            # Receive base64 frame from Flutter
            data = await websocket.receive_text()
            img = decode_base64_image(data)
            
            # Run YOLO detection
            detections = detect(img)
            
            # Base response (sent every frame)
            response = {
                "detections": detections
            }
            
            # Add detections to buffer for AI
            detection_buffer.extend(detections)
            frame_count += 1
            
            # Every 4 frames: get AI response
            if frame_count >= BUFFER_SIZE:
                ai_data = await get_ai_response(detection_buffer)
                
                if ai_data:
                    # Add AI response to this frame's response
                    response["ai_response"] = ai_data["response"]
                    response["runtime"] = ai_data["runtime"]
                    response["cache_hit"] = ai_data["cache_hit"]
                
                # Reset buffer
                detection_buffer = []
                frame_count = 0
            
            # Send response to Flutter
            await websocket.send_json(response)
    
    except WebSocketDisconnect:
        print(f"❌ Client disconnected: {websocket.client.host}")
        active_connections.remove(websocket)


# ------------------------------
# HTTP endpoint for single image detection + description
# ------------------------------
@router.post("/detect-and-describe")
async def detect_and_describe_image(file: UploadFile = File(...)):
    """
    Upload image, detect with YOLO, describe with LLM
    
    Use case:
    - Single image analysis
    - Non-real-time processing
    - Testing/debugging
    
    Combines:
    - YOLO detection (existing)
    - LLM description (new)
    
    Returns:
    {
        "detections": [...],
        "llm_descriptions": [...],
        "annotated_image": "data:image/jpeg;base64,..."
    }
    """
    try:
        # Read and decode image
        contents = await file.read()
        img_bytes = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        
        # Run YOLO detection
        detections = detect(img)
        
        # Get LLM descriptions for top 3 detections
        llm_descriptions = []
        async with httpx.AsyncClient() as client:
            for det in detections[:3]:  # Limit to top 3 to save time
                try:
                    response = await client.post(
                        "http://llm-gateway:8000/describe-detection",
                        json={
                            "object": det["label"],
                            "confidence": det["confidence"]
                        },
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        llm_data = response.json()
                        llm_descriptions.append({
                            "object": det["label"],
                            "confidence": det["confidence"],
                            "description": llm_data.get("primary", {}).get("response"),
                            "runtime": llm_data.get("primary", {}).get("runtime")
                        })
                except Exception as e:
                    llm_descriptions.append({
                        "object": det["label"],
                        "error": str(e)
                    })
        
        # Draw annotated image
        annotated = draw_detections(img.copy(), detections)
        encoded_img = encode_base64_image(annotated)
        
        return {
            "detections": detections,
            "llm_descriptions": llm_descriptions,
            "annotated_image": encoded_img
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )
