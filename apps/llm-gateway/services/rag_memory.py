"""
RAG Memory Bank for our Detection Buffer Service.

We use this exclusively on cache-miss paths inside detection_buffer.py.
We never call this on cache hits, to protect our LRU cache's hot path latency.

Two responsibilities:
1. retrieve_context: we query Pinecone for real historical patterns before
   generating a new LLM response.
2. record_event: after a response is approved by our LLM-as-a-Judge, we
   write a summary of that real event back into Pinecone, so future
   retrievals reflect genuine history instead of static seed data.
"""
import os
import json
import time
import logging
import boto3
from pinecone import Pinecone, ServerlessSpec

logger = logging.getLogger(__name__)

INDEX_NAME = "detection-memory"
EMBED_DIMENSIONS = 1024


class RAGMemoryBank:
    def __init__(self):
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.pc_api_key = os.getenv("PINECONE_API_KEY")

        if not self.pc_api_key:
            logger.warning("PINECONE_API_KEY not set. We disable RAG memory.")
            self.enabled = False
            return

        try:
            self.bedrock = boto3.client(
                "bedrock-runtime",
                region_name=self.aws_region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            )

            self.pc = Pinecone(api_key=self.pc_api_key)

            existing = [idx["name"] for idx in self.pc.list_indexes()]
            if INDEX_NAME not in existing:
                self.pc.create_index(
                    name=INDEX_NAME,
                    dimension=EMBED_DIMENSIONS,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region=self.aws_region),
                )
                logger.info(f"We created Pinecone index '{INDEX_NAME}'.")

            self.index = self.pc.Index(INDEX_NAME)
            self.enabled = True
            logger.info("RAG Memory Bank initialized successfully.")
        except Exception as e:
            logger.error(f"We failed to initialize RAG memory: {e}")
            self.enabled = False

    def _get_embedding(self, text: str) -> list:
        """We call Amazon Titan Embed V2 to vectorize our text."""
        body = json.dumps({
            "inputText": text,
            "dimensions": EMBED_DIMENSIONS,
            "normalize": True,
        })
        response = self.bedrock.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        response_body = json.loads(response.get("body").read())
        return response_body.get("embedding")

    def retrieve_context(self, bucket: str, avg_confidence: float) -> str:
        """
        We query Pinecone for the most relevant historical event in this
        confidence bucket. We only call this on cache-miss paths.
        """
        if not self.enabled:
            return ""

        try:
            query_text = f"Historical events for bucket '{bucket}' at confidence {avg_confidence*100:.1f}%."
            query_vector = self._get_embedding(query_text)

            results = self.index.query(
                vector=query_vector,
                top_k=1,
                include_metadata=True,
                filter={"bucket": {"$eq": bucket}},
            )

            if results["matches"]:
                best_match = results["matches"][0]
                if best_match["score"] > 0.5:
                    return best_match["metadata"].get("context_text", "")
            return ""
        except Exception as e:
            logger.error(f"RAG retrieval failed (non-fatal): {e}")
            return ""

    def record_event(self, bucket: str, avg_confidence: float, detection_count: int):
        """
        We record a real event summary after our Judge approves a response.
        This is what gives our memory bank genuine historical value over time.
        """
        if not self.enabled:
            return

        try:
            summary = (
                f"Bucket '{bucket}' was regenerated at {avg_confidence*100:.1f}% "
                f"average confidence, with {detection_count} detections in the batch."
            )
            vector = self._get_embedding(summary)
            self.index.upsert(vectors=[{
                "id": f"{bucket}-{int(time.time())}",
                "values": vector,
                "metadata": {"context_text": summary, "bucket": bucket},
            }])
            logger.info(f"We recorded a real event for bucket '{bucket}' in Pinecone.")
        except Exception as e:
            logger.error(f"We failed to record RAG event (non-fatal): {e}")
