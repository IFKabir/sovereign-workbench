import os
import logging
from pathlib import Path
from agent_core.state import WorkbenchState

logger = logging.getLogger(__name__)

# Lazy loaded SentenceTransformer model instance
_embedder_cache = None

def _get_embedder():
    global _embedder_cache
    if _embedder_cache is None:
        try:
            from sentence_transformers import SentenceTransformer
            root = Path(__file__).parent.parent.parent.parent.parent
            model_path = root / "models" / "bge-m3"
            if model_path.exists():
                _embedder_cache = SentenceTransformer(str(model_path))
            else:
                _embedder_cache = SentenceTransformer("BAAI/bge-m3")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ({e}). Using mock vectors.")
            _embedder_cache = False
    return _embedder_cache

def _local_fixture_search(query: str) -> list[dict]:
    """Generic token overlap search over local standard documents."""
    root = Path(__file__).parent.parent.parent.parent.parent
    fixtures_dir = root / "data" / "test-fixtures" / "standards"
    results = []
    
    if fixtures_dir.exists():
        q_words = set(query.lower().split())
        for fpath in fixtures_dir.glob("*.md"):
            try:
                content = fpath.read_text(encoding="utf-8")
                c_words = set(content.lower().split())
                overlap = len(q_words.intersection(c_words))
                if overlap > 0:
                    results.append({
                        "content": content[:1500],
                        "source": f"standards/{fpath.name}",
                        "title": fpath.name,
                        "score": float(overlap)
                    })
            except Exception as exc:
                logger.warning(f"Error reading fixture {fpath}: {exc}")
                
        results.sort(key=lambda x: x["score"], reverse=True)
    return results[:3]

async def retrieve_standards(state: WorkbenchState) -> dict:
    """Retrieves standard documents from Qdrant and populates retrieved_context & rag_context."""
    query = state.get("query", "")
    
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection = os.getenv("QDRANT_COLLECTION", "mrpl_standards")
    
    retrieved_chunks = []
    
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url=qdrant_url, timeout=3.0)
        
        embedder = _get_embedder()
        if embedder:
            vec = embedder.encode(query).tolist()
        else:
            vec = [0.0] * 1024
            
        res = client.query_points(collection_name=collection, query=vec, limit=5)
        for hit in res.points:
            payload = hit.payload or {}
            content = payload.get("content") or payload.get("text", "")
            source = payload.get("source_file") or payload.get("source", "standards")
            title = payload.get("title") or payload.get("standard_code", "Standard Document")
            if content:
                retrieved_chunks.append({
                    "content": content,
                    "source": source,
                    "title": title,
                    "score": hit.score
                })
        logger.info(f"RAG Retriever: Got {len(retrieved_chunks)} hits from Qdrant collection '{collection}'")
    except Exception as e:
        logger.warning(f"Qdrant query failed or unavailable ({e}). Falling back to local token overlap search.")
        retrieved_chunks = _local_fixture_search(query)

    if not retrieved_chunks:
        retrieved_chunks = _local_fixture_search(query)

    formatted_context_parts = []
    for chunk in retrieved_chunks:
        formatted_context_parts.append(
            f"Source: {chunk['source']}\n{chunk['content']}"
        )
        
    retrieved_context_str = "\n\n---\n\n".join(formatted_context_parts)
    
    return {
        "rag_results": {
            "retrieved_docs": [c["content"] for c in retrieved_chunks],
            "sources": [c["source"] for c in retrieved_chunks],
            "chunks": retrieved_chunks,
        },
        "retrieved_context": retrieved_context_str,
        "rag_context": retrieved_context_str,
        "current_node": "retrieve_standards"
    }
