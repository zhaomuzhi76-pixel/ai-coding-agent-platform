from __future__ import annotations

from typing import Any

import httpx

class EmbeddingService:
    """
    Ollama embedding provider.

    Responsibility:
        - generate code embeddings

    Not Responsible:
        - configuration loading
        - chunk generation
        - storage
        - retrieval
    """

    VERSION = "1.0"

    RESPONSIBILITY = (
        "code_embedding_generation"
    )

    def __init__(
        self,
        model: str,
        base_url: str,
        timeout: int,
    ) -> None:

        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def _request(
        self,
        payload: dict[str, Any],
    ) -> list[list[float]]:

        async with httpx.AsyncClient(
            timeout=self.timeout
        ) as client:

            response = await client.post(
                f"{self.base_url}/api/embed",
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

        return data["embeddings"]

    async def embed(
        self,
        text: str,
    ) -> list[float]:

        result = await self.embed_batch(
            [text]
        )

        if len(result) != 1:
            raise RuntimeError(
                "embedding response size mismatch"
            )

        return result[0]

    async def embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            raise ValueError(
                "texts must not be empty"
            )

        return await self._request(
            {
                "model":
                    self.model,

                "input":
                    texts,
            }
        )

    def ready(
        self,
    ) -> bool:

        return bool(
            self.model
            and self.base_url
        )

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "EmbeddingService",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "model":
                self.model,

            "ready":
                self.ready(),
        }

__all__ = [
    "EmbeddingService",
]
