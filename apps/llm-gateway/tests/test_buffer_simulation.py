"""
Integration tests for Detection Buffer + LRU Cache
Tests real-time detection buffering with AI response caching
"""
import pytest
import requests
import time
import random
from typing import List, Dict

BASE_URL = "http://localhost:8002"

class TestDetectionBuffer:
    """Test suite for Detection Buffer Service"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test"""
        # Clear buffer before each test
        try:
            requests.post(f"{BASE_URL}/buffer/clear")
        except:
            pass
        
        yield
        
        # Cleanup after test (optional)
        pass
    
    def generate_detection(self, confidence: float) -> dict:
        """Generate a fake detection"""
        return {
            "label": "Heart",
            "confidence": confidence,
            "bbox": [
                random.uniform(0.1, 0.4),
                random.uniform(0.1, 0.4),
                random.uniform(0.5, 0.8),
                random.uniform(0.5, 0.8)
            ]
        }
    
    def test_buffer_fills_correctly(self):
        """Test that buffer fills up to capacity before processing"""
        buffer_size = 4
        
        for i in range(buffer_size - 1):
            response = requests.post(
                f"{BASE_URL}/buffer/add-detection",
                json={"detection": self.generate_detection(0.95)}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should be buffered, not processed
            assert data['status'] == 'buffered'
            assert data['buffer_count'] == i + 1
            assert data['buffer_size'] == buffer_size
        
        # Last detection should trigger processing
        response = requests.post(
            f"{BASE_URL}/buffer/add-detection",
            json={"detection": self.generate_detection(0.95)}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have AI response now
        assert 'source' in data
        assert 'response' in data
        assert data['detection_count'] == buffer_size
    
    def test_cache_miss_then_hit(self):
        """Test that first call is cache miss, second is cache hit"""
        detections_excellent = [self.generate_detection(0.95) for _ in range(4)]
        
        # First batch - should be CACHE MISS
        for det in detections_excellent:
            requests.post(
                f"{BASE_URL}/buffer/add-detection",
                json={"detection": det}
            )
        
        # Wait a bit for processing
        time.sleep(0.5)
        
        # Check stats - should have 1 AI call, 0 cached
        stats = requests.get(f"{BASE_URL}/buffer/stats").json()
        assert stats['ai']['total_calls'] == 1
        assert stats['ai']['cached_responses'] == 0
        
        # Second batch with SAME confidence range - should be CACHE HIT
        for det in detections_excellent:
            requests.post(
                f"{BASE_URL}/buffer/add-detection",
                json={"detection": det}
            )
        
        time.sleep(0.5)
        
        # Check stats - should still have 1 AI call, but 1 cached
        stats = requests.get(f"{BASE_URL}/buffer/stats").json()
        assert stats['ai']['total_calls'] == 1  # No new calls
        assert stats['ai']['cached_responses'] == 1  # One cached response
        assert stats['cache']['hits'] == 1
    
    def test_confidence_buckets(self):
        """Test that different confidence levels use different buckets"""
        confidence_levels = [0.95, 0.80, 0.65, 0.50, 0.42]
        
        for confidence in confidence_levels:
            detections = [self.generate_detection(confidence) for _ in range(4)]
            
            for det in detections:
                requests.post(
                    f"{BASE_URL}/buffer/add-detection",
                    json={"detection": det}
                )
            
            time.sleep(0.5)
        
        # Should have 5 different AI calls (one per bucket)
        stats = requests.get(f"{BASE_URL}/buffer/stats").json()
        assert stats['ai']['total_calls'] == 5
        assert stats['cache']['current_size'] == 5  # 5 buckets cached
    
    def test_cache_hit_latency_faster(self):
        """Test that cache hits are significantly faster than API calls"""
        # First batch - cache miss
        detections = [self.generate_detection(0.95) for _ in range(4)]
        
        start = time.time()
        for det in detections:
            response = requests.post(
                f"{BASE_URL}/buffer/add-detection",
                json={"detection": det}
            )
        first_latency = (time.time() - start) * 1000
        
        time.sleep(0.5)
        
        # Second batch - cache hit
        start = time.time()
        for det in detections:
            response = requests.post(
                f"{BASE_URL}/buffer/add-detection",
                json={"detection": det}
            )
        second_latency = (time.time() - start) * 1000
        
        # Cache hit should be MUCH faster (at least 10x)
        assert second_latency < first_latency / 10
    
    def test_stats_endpoint(self):
        """Test that stats endpoint returns correct structure"""
        response = requests.get(f"{BASE_URL}/buffer/stats")
        
        assert response.status_code == 200
        stats = response.json()
        
        # Check structure
        assert 'buffer' in stats
        assert 'confidence_distribution' in stats
        assert 'ai' in stats
        assert 'latency' in stats
        assert 'cache' in stats
        
        # Check buffer structure
        assert 'size' in stats['buffer']
        assert 'current_detections' in stats['buffer']
        assert 'total_detections_processed' in stats['buffer']
        
        # Check AI structure
        assert 'total_calls' in stats['ai']
        assert 'cached_responses' in stats['ai']
        assert 'cache_hit_rate' in stats['ai']


class TestLRUCache:
    """Test suite for LRU Cache eviction policy"""
    
    def test_lru_eviction(self):
        """Test that LRU eviction works correctly when cache is full"""
        # This would require filling up the cache (capacity=20)
        # and verifying that least recently used items get evicted
        pass  # TODO: Implement when we want to test edge cases


# Manual simulation script (not a pytest, just for visual testing)
def simulate_camera_stream(num_detections: int = 20, verbose: bool = True):
    """
    Simulate camera stream with varying confidence levels
    This mimics real-world scenario where confidence varies
    """
    
    if verbose:
        print("\n" + "="*60)
        print("  DETECTION BUFFER + LRU CACHE SIMULATION")
        print("="*60 + "\n")
        print(f"🎥 Starting camera simulation...")
        print(f"   Sending {num_detections} detections (buffer_size=4)")
        print(f"   Watch for CACHE HITS!\n")
    
    # Simulate different confidence scenarios
    confidence_scenarios = [
        0.95, 0.93, 0.92, 0.91,  # Excellent (4x)
        0.80, 0.82, 0.78, 0.76,  # Good (4x)
        0.65, 0.67, 0.63, 0.61,  # Moderate (4x)
        0.50, 0.52,              # Acceptable (2x)
        0.42, 0.43,              # Threshold (2x)
        0.35, 0.30,              # Rejected (2x)
        0.94, 0.81,              # Back to cached buckets (2x)
    ]
    
    def generate_detection(confidence: float) -> dict:
        return {
            "label": "Heart",
            "confidence": confidence,
            "bbox": [
                random.uniform(0.1, 0.4),
                random.uniform(0.1, 0.4),
                random.uniform(0.5, 0.8),
                random.uniform(0.5, 0.8)
            ]
        }
    
    response_times = []
    
    for i, confidence in enumerate(confidence_scenarios[:num_detections], 1):
        detection = generate_detection(confidence)
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"📸 Detection {i}/{num_detections} - Confidence: {confidence:.2f}")
            print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{BASE_URL}/buffer/add-detection",
                json={"detection": detection},
                timeout=10
            )
            
            latency = (time.time() - start_time) * 1000
            response_times.append(latency)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'source' in data:
                    source = data['source']
                    ai_response = data['response']
                    ai_latency = data['latency_ms']
                    bucket = data['confidence_bucket']
                    
                    if verbose:
                        if source == 'cache':
                            print(f"✅ CACHE HIT! ({bucket})")
                            print(f"   ⚡ Latency: {ai_latency:.2f}ms (INSTANT!)")
                        else:
                            print(f"❌ CACHE MISS ({bucket})")
                            print(f"   🐌 Latency: {ai_latency:.2f}ms (Gemini API call)")
                        
                        print(f"   🤖 AI Response: {ai_response}")
                else:
                    if verbose:
                        print(f"📦 Buffered: {data['buffer_count']}/{data['buffer_size']}")
            
        except Exception as e:
            if verbose:
                print(f"❌ Exception: {e}")
        
        time.sleep(0.05)  # Simulate 30 FPS camera
    
    # Final stats
    if verbose:
        print(f"\n{'='*60}")
        print("📊 FINAL STATISTICS")
        print(f"{'='*60}\n")
        
        try:
            stats = requests.get(f"{BASE_URL}/buffer/stats").json()
            
            print(f"📦 Buffer Stats:")
            print(f"   Total detections: {stats['buffer']['total_detections_processed']}")
            
            print(f"\n🎯 Confidence Distribution:")
            for bucket, count in stats['confidence_distribution'].items():
                print(f"   {bucket:12s}: {count:3d} detections")
            
            print(f"\n🤖 AI Calls:")
            print(f"   Total Gemini calls: {stats['ai']['total_calls']}")
            print(f"   Cached responses:   {stats['ai']['cached_responses']}")
            print(f"   Cache hit rate:     {stats['ai']['cache_hit_rate']:.1f}%")
            
            print(f"\n⚡ Latency:")
            print(f"   Avg cache hit:    {stats['latency']['avg_cache_hit_ms']:.2f}ms")
            print(f"   Avg Gemini call:  {stats['latency']['avg_gemini_call_ms']:.2f}ms")
            if stats['latency']['speedup_factor'] > 0:
                print(f"   Speedup factor:   {stats['latency']['speedup_factor']:.0f}x")
            
            print(f"\n💾 Cache:")
            print(f"   Size: {stats['cache']['current_size']}/{stats['cache']['capacity']}")
            print(f"   Hit rate: {stats['cache']['hit_rate_percentage']:.1f}%")
            
            if stats['cache']['bucket_stats']:
                print(f"\n📊 Cached Buckets:")
                for bucket, bucket_stats in stats['cache']['bucket_stats'].items():
                    print(f"   {bucket:12s}: {bucket_stats['hit_count']:3d} hits")
            
        except Exception as e:
            print(f"❌ Error fetching stats: {e}")
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        print(f"\n🎯 Overall Avg Response: {avg_response_time:.2f}ms")
        print(f"\n{'='*60}")
        print("✅ Simulation Complete!")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    # Run manual simulation when script is executed directly
    simulate_camera_stream(num_detections=20)
