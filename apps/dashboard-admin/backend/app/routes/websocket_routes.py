from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
import numpy as np
import cv2
import base64
import httpx
from detection_model.detector import detect  # my TFLite detection function

router = APIRouter(
    prefix="/ws",
    tags=["websocket"]
)

active_connections: list[WebSocket] = []


# ------------------------------
# Helper to decode base64 image
# ------------------------------
def decode_base64_image(data: str) -> np.ndarray:
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
    _, buffer = cv2.imencode(".jpg", img)
    base64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_str}"


# ------------------------------
# Draw detection boxes
# ------------------------------
def draw_detections(img: np.ndarray, detections: list) -> np.ndarray:
    for det in detections:
        # Expected detection format from your detect() function
        # e.g. {"bbox": [x1, y1, x2, y2], "label": "person", "confidence": 0.85}
        bbox = det.get("bbox", [])
        label = det.get("label", "object")
        conf = det.get("confidence", 0.0)

        if len(bbox) == 4:
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            text = f"{label} {conf:.2f}"
            cv2.putText(img, text, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return img


# ------------------------------
# WebSocket endpoint
# ------------------------------
@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    print(f"✅ Client connected: {websocket.client.host}")

    try:
        while True:
            # Receive base64 frame
            data = await websocket.receive_text()
            img = decode_base64_image(data)

            # Run detection
            results = detect(img)  # should return list of dicts (with bbox, label, confidence)

            # Draw boxes
            annotated = draw_detections(img.copy(), results)

            # Encode annotated frame
            encoded_img = encode_base64_image(annotated)

            # Send back both detection data and annotated image
            await websocket.send_json({
                "detections": results,
                "annotated_frame": encoded_img
            })

    except WebSocketDisconnect:
        print(f"❌ Client disconnected: {websocket.client.host}")
        active_connections.remove(websocket)

@router.post("/detect-and-describe")
async def detect_and_describe_image(file: UploadFile = File(...)):
    """
    Upload image, detect with YOLO, describe with LLM.
    
    Combines:
    - YOLO detection (existing)
    - LLM description (new)
    """
    try:
        # Read image
        contents = await file.read()
        img_bytes = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        
        # Run YOLO detection
        detections = detect(img)
        
        # Get LLM descriptions for top 3 detections
        llm_descriptions = []
        async with httpx.AsyncClient() as client:
            for det in detections[:3]:  # Limit to save time
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
