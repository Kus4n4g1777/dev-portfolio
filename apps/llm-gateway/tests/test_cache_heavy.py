"""
Test optimizado para demostrar CACHE HITS masivos
"""
import requests
import time
import random

BASE_URL = "http://localhost:8002"

def test_massive_cache_hits():
    """
    Simula MUCHAS detecciones en pocos buckets
    Esto maximiza cache hits
    """
    
    print("\n" + "="*60)
    print("  MASSIVE CACHE HITS TEST")
    print("="*60 + "\n")
    
    # Confidence scenarios - MUCHAS REPETICIONES de cada bucket
    confidence_scenarios = [
        # 12x excellent (solo 1 miss, 11 hits!)
        0.95, 0.93, 0.92, 0.91,  # Primera vez - MISS
        0.94, 0.96, 0.93, 0.95,  # Cache HIT x4
        0.92, 0.91, 0.94, 0.93,  # Cache HIT x4
        
        # 12x good (solo 1 miss, 11 hits!)
        0.80, 0.82, 0.78, 0.76,  # Primera vez - MISS
        0.81, 0.79, 0.77, 0.80,  # Cache HIT x4
        0.82, 0.78, 0.81, 0.79,  # Cache HIT x4
        
        # 12x moderate (solo 1 miss, 11 hits!)
        0.65, 0.67, 0.63, 0.61,  # Primera vez - MISS
        0.66, 0.64, 0.62, 0.65,  # Cache HIT x4
        0.67, 0.63, 0.66, 0.64,  # Cache HIT x4
    ]
    
    cache_hits = 0
    cache_misses = 0
    
    for i, confidence in enumerate(confidence_scenarios, 1):
        detection = {
            "label": "Heart",
            "confidence": confidence,
            "bbox": [random.uniform(0.1, 0.4), random.uniform(0.1, 0.4),
                    random.uniform(0.5, 0.8), random.uniform(0.5, 0.8)]
        }
        
        print(f"Detection {i}/{len(confidence_scenarios)} - Confidence: {confidence:.2f}", end=" → ")
        
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/buffer/add-detection",
            json={"detection": detection}
        )
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            
            if 'source' in data:
                if data['source'] == 'cache':
                    cache_hits += 1
                    print(f"✅ CACHE HIT ({data['latency_ms']:.2f}ms)")
                else:
                    cache_misses += 1
                    print(f"❌ CACHE MISS ({data['latency_ms']:.2f}ms)")
            else:
                print("📦 Buffered")
        
        time.sleep(0.05)
    
    # Stats
    stats = requests.get(f"{BASE_URL}/buffer/stats").json()
    
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}\n")
    
    print(f"📦 Total detections: {stats['buffer']['total_detections_processed']}")
    print(f"\n🎯 Confidence Distribution:")
    for bucket, count in stats['confidence_distribution'].items():
        if count > 0:
            print(f"   {bucket:12s}: {count:3d} detections")
    
    print(f"\n🤖 AI Calls:")
    print(f"   Gemini calls:     {stats['ai']['total_calls']}")
    print(f"   Cached responses: {stats['ai']['cached_responses']}")
    print(f"   Cache hit rate:   {stats['ai']['cache_hit_rate']:.1f}%")
    
    print(f"\n⚡ Latency:")
    print(f"   Avg cache hit:   {stats['latency']['avg_cache_hit_ms']:.2f}ms")
    print(f"   Avg Gemini call: {stats['latency']['avg_gemini_call_ms']:.2f}ms")
    print(f"   Speedup factor:  {stats['latency']['speedup_factor']:.0f}x")
    
    print(f"\n💾 Cache:")
    print(f"   Hit rate: {stats['cache']['hit_rate_percentage']:.1f}%")
    
    if 'llm_router' in stats:
        print(f"\n🔄 LLM Router:")
        print(f"   Calls by runtime: {stats['llm_router']['calls_by_runtime']}")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    test_massive_cache_hits()
