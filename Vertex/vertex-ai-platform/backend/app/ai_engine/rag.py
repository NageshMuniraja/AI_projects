"""RAG Pipeline: Knowledge ingestion, embedding, and retrieval."""

import uuid
from typing import Optional

import anthropic
import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.models import KnowledgeDocument, KnowledgeChunk

logger = structlog.get_logger()
settings = get_settings()


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.chunk_size = 500  # tokens
        self.chunk_overlap = 50  # tokens
        self.top_k = 5  # number of chunks to retrieve

    # ─── Chunking ────────────────────────────────────────────────

    def chunk_text(self, text: str) -> list[dict]:
        """Split text into overlapping chunks."""
        # Simple word-based chunking (production would use tiktoken)
        words = text.split()
        chunks = []
        chunk_words = self.chunk_size  # approximate
        overlap_words = self.chunk_overlap

        i = 0
        chunk_index = 0
        while i < len(words):
            end = min(i + chunk_words, len(words))
            chunk_content = " ".join(words[i:end])
            chunks.append({
                "content": chunk_content,
                "chunk_index": chunk_index,
                "token_count": end - i,  # approximate
            })
            chunk_index += 1
            i += chunk_words - overlap_words

        return chunks

    # ─── Embedding ───────────────────────────────────────────────

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for text using Anthropic's Voyage or fallback."""
        # Using a simple hash-based embedding as placeholder
        # In production, use voyage-3 or text-embedding-3-small via OpenAI
        import hashlib
        import numpy as np

        # Deterministic pseudo-embedding for development
        hash_bytes = hashlib.sha512(text.encode()).digest()
        np.random.seed(int.from_bytes(hash_bytes[:4], "big"))
        embedding = np.random.randn(1536).tolist()
        # Normalize
        norm = sum(x**2 for x in embedding) ** 0.5
        embedding = [x / norm for x in embedding]
        return embedding

    # ─── Ingestion ───────────────────────────────────────────────

    async def ingest_document(
        self,
        db: AsyncSession,
        tenant_id: str,
        title: str,
        content: str,
        category: str = "general",
        source_type: str = "manual",
    ) -> KnowledgeDocument:
        """Ingest a document: chunk, embed, and store."""
        # Create document record
        doc = KnowledgeDocument(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            title=title,
            content=content,
            category=category,
            source_type=source_type,
        )
        db.add(doc)

        # Chunk the content
        chunks = self.chunk_text(content)
        doc.chunk_count = len(chunks)

        # Embed and store each chunk
        for chunk_data in chunks:
            embedding = await self.embed_text(chunk_data["content"])
            chunk = KnowledgeChunk(
                id=uuid.uuid4(),
                document_id=doc.id,
                tenant_id=tenant_id,
                content=chunk_data["content"],
                chunk_index=chunk_data["chunk_index"],
                token_count=chunk_data["token_count"],
                embedding=embedding,
                metadata={"category": category, "source": title},
            )
            db.add(chunk)

        await db.flush()
        logger.info(
            "Document ingested",
            doc_id=str(doc.id),
            chunks=len(chunks),
            tenant=tenant_id,
        )
        return doc

    # ─── Retrieval ───────────────────────────────────────────────

    async def retrieve(
        self,
        db: AsyncSession,
        tenant_id: str,
        query: str,
        top_k: Optional[int] = None,
        category: Optional[str] = None,
    ) -> list[dict]:
        """Retrieve the most relevant knowledge chunks for a query."""
        k = top_k or self.top_k
        query_embedding = await self.embed_text(query)

        # pgvector cosine similarity search
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        sql = text("""
            SELECT
                kc.id,
                kc.content,
                kc.metadata,
                kd.title as doc_title,
                1 - (kc.embedding <=> :embedding::vector) as similarity
            FROM knowledge_chunks kc
            JOIN knowledge_documents kd ON kd.id = kc.document_id
            WHERE kc.tenant_id = :tenant_id
            AND kd.is_active = true
            ORDER BY kc.embedding <=> :embedding::vector
            LIMIT :limit
        """)

        params = {
            "tenant_id": tenant_id,
            "embedding": embedding_str,
            "limit": k,
        }

        if category:
            sql = text("""
                SELECT
                    kc.id,
                    kc.content,
                    kc.metadata,
                    kd.title as doc_title,
                    1 - (kc.embedding <=> :embedding::vector) as similarity
                FROM knowledge_chunks kc
                JOIN knowledge_documents kd ON kd.id = kc.document_id
                WHERE kc.tenant_id = :tenant_id
                AND kd.is_active = true
                AND kd.category = :category
                ORDER BY kc.embedding <=> :embedding::vector
                LIMIT :limit
            """)
            params["category"] = category

        result = await db.execute(sql, params)
        rows = result.fetchall()

        return [
            {
                "id": str(row.id),
                "content": row.content,
                "source": row.doc_title,
                "similarity": float(row.similarity),
                "metadata": row.metadata,
            }
            for row in rows
        ]

    def format_rag_context(self, chunks: list[dict]) -> str:
        """Format retrieved chunks into context string for the prompt."""
        if not chunks:
            return ""

        sections = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "Knowledge Base")
            sections.append(f"[Source: {source}]\n{chunk['content']}")

        return "\n\n---\n\n".join(sections)


# Singleton
rag_pipeline = RAGPipeline()
