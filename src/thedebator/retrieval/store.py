"""Vector store management using ChromaDB."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional

import chromadb
from chromadb.config import Settings

# Disable ChromaDB anonymized telemetry for local CLI runs so the project
# doesn't attempt to send telemetry (which can require network access and an
# API key). We do this at runtime before any client is created.
# Note: we will explicitly set anonymized_telemetry=False on the Settings
# used to construct the client so telemetry won't be sent for this client.

from .types import DocumentChunk


@dataclass
class VectorStore:
    """Wrapper around ChromaDB client managing document chunks."""

    persist_directory: Path
    collection_name: str = "debate"
    _client: Optional[chromadb.Client] = field(init=False, repr=False, default=None)

    def __post_init__(self) -> None:
        self.persist_directory = Path(self.persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        # Create a Settings instance with telemetry disabled so the ChromaDB
        # System created by chromadb.Client will not attempt to send events.
        settings = Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=str(self.persist_directory),
            anonymized_telemetry=False,
        )

        self._client = chromadb.Client(settings)

    def reset(self) -> None:
        """Drop the existing collection if present."""
        if not self._client:
            return
        existing = {col.name for col in self._client.list_collections()}
        if self.collection_name in existing:
            self._client.delete_collection(self.collection_name)

    def upsert(self, chunks: Iterable[DocumentChunk]) -> int:
        if not self._client:
            raise RuntimeError("VectorStore client is not initialized")
        collection = self._client.get_or_create_collection(self.collection_name)

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[dict] = []

        for chunk in chunks:
            ids.append(chunk.chunk_id)
            documents.append(chunk.content)
            metadatas.append({"page": chunk.page})

        if ids:
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

        return len(ids)

    def similarity_search(self, query: str, k: int = 3) -> List[DocumentChunk]:
        if not self._client:
            return []
        collection = self._client.get_or_create_collection(self.collection_name)
        results = collection.query(query_texts=[query], n_results=k)

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        chunks: List[DocumentChunk] = []
        for chunk_id, content, metadata in zip(ids, documents, metadatas):
            page = int(metadata.get("page", 0)) if isinstance(metadata, dict) else 0
            chunks.append(DocumentChunk(chunk_id=chunk_id, content=content, page=page))
        return chunks
