"""
Test para ver las diferentes "personalidades" de cada LLM
"""
import requests
import time

BASE_URL = "http://localhost:8002"

def test_personalities():
    """Ver cómo responde cada LLM al mismo prompt"""
    
    requests.post(f"{BASE_URL}/buffer/clear")
    
    print("\n" + "="*60)
    print("  TESTING LLM PERSONALITIES")
    print("="*60 + "\n")
    
    # Usar DIFERENTES confidence levels para evitar cache
    confidence_levels = [
        (0.95, "excellent", "Gemini 2.5 Flash"),
        (0.80, "good", "Dart"),
        (0.65, "moderate", "Go"),
    ]
    
    for idx, (confidence, bucket, expected_runtime) in enumerate(confidence_levels, 1):
        print(f"\n{'='*60}")
        print(f"Test {idx}: {bucket.upper()} bucket (confidence: {confidence})")
        print(f"Expected runtime: {expected_runtime}")
        print(f"{'='*60}")
        
        # Send 4 detections para llenar el buffer
        for j in range(4):
            detection = {
                "label": "Heart",
                "confidence": confidence,
                "bbox": [0.1, 0.2, 0.3, 0.4]
            }
            
            response = requests.post(
                f"{BASE_URL}/buffer/add-detection",
                json={"detection": detection}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'source' in data:
                    source = data.get('source', 'unknown')
                    runtime = data.get('runtime', 'unknown')
                    ai_response = data.get('response', '')
                    latency = data.get('latency_ms', 0)
                    bucket_name = data.get('confidence_bucket', 'unknown')
                    
                    print(f"\n  Source: {source}")
                    print(f"  Runtime: {runtime}")
                    print(f"  Bucket: {bucket_name}")
                    print(f"  Latency: {latency:.2f}ms")
                    print(f"  Response: {ai_response}")
        
        time.sleep(0.2)
    
    # Stats finales
    print(f"\n{'='*60}")
    print("FINAL STATS")
    print(f"{'='*60}")
    
    stats = requests.get(f"{BASE_URL}/buffer/stats").json()
    
    print(f"\n🔄 LLM Router:")
    router_stats = stats.get('llm_router', {})
    calls = router_stats.get('calls_by_runtime', {})
    for runtime, count in calls.items():
        if count > 0:
            print(f"   {runtime}: {count} calls")
    
    print(f"\n💾 Cache:")
    print(f"   Hit rate: {stats['cache']['hit_rate_percentage']:.1f}%")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    test_personalities()
