"""
Integration test: verifies that EVERY runtime in the LLM Router's rotation
gets invoked at least once across a full cycle.

Strategy:
- Clear the buffer/cache before starting (does NOT reset the router's
  rotation index, which is exactly what we want to exercise).
- Send N full batches (buffer_size=4) using DIFFERENT confidence values
  per batch, so each batch is guaranteed to be a cache MISS and therefore
  actually reaches the LLM Router (cache hits never touch the router).
- After N batches (N = len(rotation)), assert that every runtime name in
  the rotation shows up at least once in llm_router.calls_by_runtime
  (or, for runtimes that legitimately fail in this environment, that they
  were at least attempted — see NOTE below).
"""
import pytest
import requests
import time

BASE_URL = "http://localhost:8002"

# Confidence values chosen to land in DIFFERENT buckets each time,
# guaranteeing cache misses across the whole run.
# Buckets: excellent(>=.90) good(>=.75) moderate(>=.60) acceptable(>=.45)
#          threshold(>=.40) rejected(<.40)
CONFIDENCE_SEQUENCE = [0.95, 0.80, 0.65, 0.50, 0.42, 0.35, 0.93, 0.78]


class TestFullRotation:

    @pytest.fixture(autouse=True)
    def clear_cache_only(self):
        """
        Clear buffer + cache before the test, but do NOT care about the
        router's current rotation index — we want to pick up wherever it
        left off, since the rotation is a continuous cycle by design.
        """
        try:
            requests.post(f"{BASE_URL}/buffer/clear")
        except Exception:
            pass
        time.sleep(0.5)
        yield

    def _send_batch(self, confidence: float) -> dict:
        """Send 4 detections (one full buffer) at a fixed confidence."""
        last_response = None
        for _ in range(4):
            r = requests.post(
                f"{BASE_URL}/buffer/add-detection",
                json={
                    "detection": {
                        "label": "Heart",
                        "confidence": confidence,
                        "bbox": [0.1, 0.2, 0.3, 0.4],
                    }
                },
            )
            assert r.status_code == 200
            last_response = r.json()
        return last_response

    def test_every_runtime_gets_invoked_across_full_cycle(self):
        """
        Send one full cycle worth of cache-missing batches and confirm
        every runtime in the rotation was attempted at least once.
        """
        stats_before = requests.get(f"{BASE_URL}/buffer/stats").json()
        rotation_len = len(stats_before["llm_router"]["calls_by_runtime"]) \
            + 0  # calls_by_runtime is keyed by all rotation members

        expected_runtimes = set(stats_before["llm_router"]["calls_by_runtime"].keys())

        results = []
        for i in range(len(expected_runtimes)):
            confidence = CONFIDENCE_SEQUENCE[i % len(CONFIDENCE_SEQUENCE)]
            result = self._send_batch(confidence)
            results.append(result)
            time.sleep(0.3)

        stats_after = requests.get(f"{BASE_URL}/buffer/stats").json()
        calls = stats_after["llm_router"]["calls_by_runtime"]
        failures = stats_after["llm_router"]["failures_by_runtime"]

        print("\n" + "=" * 60)
        print("FULL ROTATION CYCLE RESULTS")
        print("=" * 60)
        for runtime in expected_runtimes:
            print(
                f"  {runtime:20s} | calls: {calls.get(runtime, 0):2d} "
                f"| failures: {failures.get(runtime, 0):2d}"
            )
        print("=" * 60 + "\n")

        # NOTE: in this local dev environment, "dart" and "ollama" are only
        # reachable from inside the Docker network — when this test runs
        # from the host, those two legitimately fail and fall back. We still
        # assert they were ATTEMPTED (call OR failure count > 0), which is
        # the real thing this test is verifying: that the round-robin index
        # actually visits every runtime, rather than skipping any of them.
        for runtime in expected_runtimes:
            attempted = calls.get(runtime, 0) + failures.get(runtime, 0)
            assert attempted > 0, (
                f"Runtime '{runtime}' was never attempted during a full "
                f"rotation cycle — round-robin index is skipping it."
            )

        # Bedrock specifically must have succeeded (not just been attempted),
        # since it's a real external call we care about validating end-to-end.
        assert calls.get("bedrock-nova", 0) > 0, (
            "bedrock-nova was attempted but never succeeded — check AWS "
            "credentials, model access, or payload format."
        )
