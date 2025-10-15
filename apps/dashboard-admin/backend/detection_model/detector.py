import os
import numpy as np
from tflite_runtime.interpreter import Interpreter
import cv2

# ------------------------------
# Load the TFLite model
# ------------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), "best_float32.tflite")
LABELS_PATH = os.path.join(os.path.dirname(__file__), "labels.txt")

interpreter = Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

# Load labels
with open(LABELS_PATH, "r") as f:
    labels = [line.strip() for line in f.readlines()]

# Get input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print(f"[DEBUG] Model input shape: {input_details[0]['shape']}")
print(f"[DEBUG] Model output shape: {output_details[0]['shape']}")


def letterbox(img, new_shape=(640, 640), color=(114, 114, 114)):
    """
    Resize image with letterbox (maintain aspect ratio, pad with gray bars).
    Returns the resized image and the scaling parameters.
    """
    shape = img.shape[:2]  # current shape [height, width]
    
    print(f"[DEBUG] Original image shape: {shape[1]}x{shape[0]} (WxH)")
    
    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    
    # Compute padding
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))  # (width, height)
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding
    
    dw /= 2  # divide padding into 2 sides
    dh /= 2
    
    print(f"[DEBUG] Scale ratio: {r}")
    print(f"[DEBUG] New unpadded size: {new_unpad[0]}x{new_unpad[1]} (WxH)")
    print(f"[DEBUG] Padding: left/right={dw}, top/bottom={dh}")
    
    # Resize
    if shape[::-1] != new_unpad:  # if not already the right size
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    
    # Add border (letterbox)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    
    return img, r, (dw, dh)


# ------------------------------
# Detection function
# ------------------------------
def detect(image: np.ndarray) -> list:
    """
    Perform detection on a single image (numpy array).

    Args:
        image (np.ndarray): Input image in shape (H, W, C), dtype=np.uint8 or np.float32

    Returns:
        list: Detection results with bounding boxes in normalized [x1, y1, x2, y2] format
    """
    # Get original image dimensions
    orig_h, orig_w = image.shape[:2]
    print(f"\n[DEBUG] ===== NEW DETECTION =====")
    print(f"[DEBUG] Input image size: {orig_w}x{orig_h} (WxH)")
    
    # Preprocess image: resize to input size of the model with letterbox
    input_shape = input_details[0]['shape']  # e.g., [1, 640, 640, 3]
    input_height, input_width = input_shape[1], input_shape[2]

    # Apply letterbox preprocessing (same as training)
    img_resized, ratio, (pad_w, pad_h) = letterbox(image, (input_height, input_width))
    img_resized = img_resized.astype(np.float32) / 255.0  # scale 0-1

    # Add batch dimension
    input_data = np.expand_dims(img_resized, axis=0)

    # Set the tensor
    interpreter.set_tensor(input_details[0]['index'], input_data)

    # Run inference
    interpreter.invoke()

    # Get output
    output_data = interpreter.get_tensor(output_details[0]['index'])

    # Transpose to shape (8400, 6) for easier unpacking
    predictions = output_data[0].T  # (6, 8400) -> (8400, 6)

    detections_list = []
    detection_count = 0
    
    for det in predictions:
        confidence = float(det[4])
        if confidence < 0.4:  # optional threshold
            continue
        
        class_idx = int(det[5])
        
        # Coordinates are normalized [0-1] in the LETTERBOXED 640x640 space
        # First convert to pixels in 640x640 space
        cx_letterbox_norm = float(det[0])  # normalized 0-1 in 640x640
        cy_letterbox_norm = float(det[1])
        w_letterbox_norm = float(det[2])
        h_letterbox_norm = float(det[3])
        
        # Convert to pixels in 640x640 letterbox space
        cx_letterbox_px = cx_letterbox_norm * input_width
        cy_letterbox_px = cy_letterbox_norm * input_height
        w_letterbox_px = w_letterbox_norm * input_width
        h_letterbox_px = h_letterbox_norm * input_height
        
        print(f"\n[DEBUG] Detection {detection_count}: {labels[class_idx]} ({confidence:.2f})")
        print(f"  Normalized in 640x640: ({cx_letterbox_norm:.3f}, {cy_letterbox_norm:.3f}, {w_letterbox_norm:.3f}, {h_letterbox_norm:.3f})")
        print(f"  Pixels in 640x640: ({cx_letterbox_px:.1f}, {cy_letterbox_px:.1f}, {w_letterbox_px:.1f}, {h_letterbox_px:.1f})")
        
        # Remove letterbox padding to get coordinates in the scaled (but not padded) image
        cx_scaled = cx_letterbox_px - pad_w
        cy_scaled = cy_letterbox_px - pad_h
        w_scaled = w_letterbox_px
        h_scaled = h_letterbox_px
        
        print(f"  After removing padding: ({cx_scaled:.1f}, {cy_scaled:.1f}, {w_scaled:.1f}, {h_scaled:.1f})")
        
        # Scale back to original image coordinates
        cx_original = cx_scaled / ratio
        cy_original = cy_scaled / ratio
        w_original = w_scaled / ratio
        h_original = h_scaled / ratio
        
        print(f"  In original image space: ({cx_original:.1f}, {cy_original:.1f}, {w_original:.1f}, {h_original:.1f})")
        
        # Convert from center format to corner format
        x1 = cx_original - w_original / 2
        y1 = cy_original - h_original / 2
        x2 = cx_original + w_original / 2
        y2 = cy_original + h_original / 2
        
        print(f"  Corner format (pixels): ({x1:.1f}, {y1:.1f}) to ({x2:.1f}, {y2:.1f})")
        
        # Normalize to [0, 1] based on original image size
        x1_norm = x1 / orig_w
        y1_norm = y1 / orig_h
        x2_norm = x2 / orig_w
        y2_norm = y2 / orig_h
        
        print(f"  Normalized: ({x1_norm:.3f}, {y1_norm:.3f}) to ({x2_norm:.3f}, {y2_norm:.3f})")
        
        # Clip to valid range
        x1_norm = max(0, min(1, x1_norm))
        y1_norm = max(0, min(1, y1_norm))
        x2_norm = max(0, min(1, x2_norm))
        y2_norm = max(0, min(1, y2_norm))
        
        print(f"  After clipping: ({x1_norm:.3f}, {y1_norm:.3f}) to ({x2_norm:.3f}, {y2_norm:.3f})")
        
        detections_list.append({
            "label": labels[class_idx],
            "confidence": confidence,
            "bbox": [x1_norm, y1_norm, x2_norm, y2_norm]  # normalized corner format
        })
        
        detection_count += 1

    print(f"\n[DEBUG] Total detections: {detection_count}")
    return detections_list