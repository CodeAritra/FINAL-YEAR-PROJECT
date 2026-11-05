"""
Qdrant Cloud Client & Vector Database Manager.
Handles collection creation, point upsertion, and semantic vector search.
Supports Qdrant Cloud as primary, with graceful in-memory fallback for offline testing.
"""

from typing import Any
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from config import settings

logger = logging.getLogger(__name__)


class QdrantManager:
    """Manages Qdrant Cloud vector collections for baseline and secured RAG pipelines."""

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        in_memory: bool = False,
    ):
        self.url = url or settings.qdrant_url
        self.api_key = api_key or settings.qdrant_api_key
        self.in_memory = in_memory

        if self.in_memory:
            logger.info("Initializing in-memory Qdrant client (test mode).")
            self.client = QdrantClient(location=":memory:")
        elif self.api_key and "cloud.qdrant.io" in self.url:
            logger.info(f"Connecting to Qdrant Cloud at {self.url}.")
            self.client = QdrantClient(url=self.url, api_key=self.api_key, timeout=10.0)
        else:
            # Check if local or custom server is responsive before blocking
            is_alive = False
            try:
                import httpx
                resp = httpx.get(f"{self.url.rstrip('/')}/readyz", timeout=0.8)
                is_alive = resp.status_code == 200
            except Exception:
                is_alive = False

            if is_alive:
                logger.info(f"Connecting to active Qdrant instance at {self.url}.")
                self.client = QdrantClient(url=self.url, api_key=self.api_key, timeout=5.0)
            else:
                logger.info(
                    "Qdrant server at %s unreachable or credentials not provided. Using in-memory store.",
                    self.url,
                )
                self.client = QdrantClient(location=":memory:")

    def ensure_collection(
        self,
        collection_name: str,
        vector_size: int = 384,
        distance: models.Distance = models.Distance.COSINE,
    ) -> bool:
        """Create collection if it does not already exist."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            if not exists:
                logger.info(f"Creating collection '{collection_name}' with size {vector_size}.")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=vector_size, distance=distance),
                )
            return True
        except Exception as e:
            logger.error(f"Error checking/creating collection '{collection_name}': {e}")
            raise

    def upsert_points(
        self,
        collection_name: str,
        points: list[dict[str, Any]],
    ) -> int:
        """
        Upsert a batch of points into the specified collection.
        Expected point format:
            {
                "id": str | int,
                "vector": list[float],
                "payload": dict
            }
        """
        if not points:
            return 0

        qdrant_points = [
            models.PointStruct(
                id=p["id"],
                vector=p["vector"],
                payload=p.get("payload", {}),
            )
            for p in points
        ]

        self.client.upsert(
            collection_name=collection_name,
            points=qdrant_points,
            wait=True,
        )
        logger.info(f"Successfully upserted {len(points)} points into '{collection_name}'.")
        return len(points)

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 4,
        score_threshold: float | None = None,
        filter_conditions: models.Filter | None = None,
    ) -> list[dict[str, Any]]:
        """Perform semantic similarity search."""
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_conditions,
            )
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload or {},
                }
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Search failed in collection '{collection_name}': {e}")
            return []

    def get_collection_info(self, collection_name: str) -> dict[str, Any]:
        """Retrieve collection metrics, point count, and status."""
        try:
            info = self.client.get_collection(collection_name)
            return {
                "status": info.status,
                "vectors_count": info.vectors_count or info.points_count or 0,
                "points_count": info.points_count or 0,
            }
        except Exception as e:
            logger.warning(f"Could not retrieve info for '{collection_name}': {e}")
            return {"status": "unknown", "vectors_count": 0, "points_count": 0}

    def delete_collection(self, collection_name: str) -> bool:
        """Delete collection and all contained points."""
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection '{collection_name}'.")
            return True
        except Exception as e:
            logger.warning(f"Failed to delete collection '{collection_name}': {e}")
            return False

