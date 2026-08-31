"""Seed Qdrant vector database with refinery test documents.

Reads test fixtures from data/test-fixtures/standards/ and embeds them
using BGE-M3 into a local Qdrant instance for RAG retrieval testing.

Usage:
    python scripts/seed_vectordb.py [--qdrant-url http://localhost:6333]

SIH26117 · MRPL · Zero Network Egress
"""

import os
import sys
import json
import uuid
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[dict]:
    """Split text into overlapping chunks preserving paragraph boundaries."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    chunk_idx = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) + 2 > chunk_size and current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "chunk_index": chunk_idx,
            })
            chunk_idx += 1
            # Keep overlap from end of previous chunk
            words = current_chunk.split()
            overlap_words = words[-overlap:] if len(words) > overlap else words
            current_chunk = " ".join(overlap_words) + "\n\n" + para
        else:
            current_chunk += ("\n\n" if current_chunk else "") + para

    if current_chunk.strip():
        chunks.append({
            "text": current_chunk.strip(),
            "chunk_index": chunk_idx,
        })

    return chunks


def load_fixtures(fixtures_dir: Path) -> list[dict]:
    """Load and chunk all test fixture documents."""
    documents = []

    standards_dir = fixtures_dir / "standards"
    if standards_dir.exists():
        for filepath in sorted(standards_dir.glob("*.md")):
            content = filepath.read_text(encoding="utf-8")
            # Extract standard code from filename
            basename = filepath.stem
            if "oisd_118" in basename:
                standard_code = "OISD-118"
                title = "OISD Standard 118 — Layouts for Oil and Gas Installations"
            elif "oisd_105" in basename:
                standard_code = "OISD-STD-105"
                title = "OISD Standard 105 — Work Permit System"
            elif "api_520" in basename:
                standard_code = "API-520"
                title = "API 520 — Sizing, Selection, and Installation of Pressure-Relieving Devices"
            else:
                standard_code = basename.upper()
                title = basename.replace("_", " ").title()

            chunks = chunk_text(content)
            for chunk in chunks:
                doc_id = hashlib.sha256(
                    f"{filepath.name}:{chunk['chunk_index']}".encode()
                ).hexdigest()[:16]

                documents.append({
                    "doc_id": doc_id,
                    "title": title,
                    "content": chunk["text"],
                    "source_file": str(filepath.relative_to(fixtures_dir)),
                    "standard_code": standard_code,
                    "chunk_index": chunk["chunk_index"],
                })

    # Also load schematic descriptions for cross-reference
    schematics_dir = fixtures_dir / "schematics"
    if schematics_dir.exists():
        for filepath in sorted(schematics_dir.glob("*.txt")):
            content = filepath.read_text(encoding="utf-8")
            doc_id = hashlib.sha256(filepath.name.encode()).hexdigest()[:16]
            documents.append({
                "doc_id": doc_id,
                "title": f"P&ID Schematic — {filepath.stem.replace('_', ' ').title()}",
                "content": content,
                "source_file": str(filepath.relative_to(fixtures_dir)),
                "standard_code": None,
                "chunk_index": 0,
            })

    return documents


def embed_documents(documents: list[dict], model_path: str) -> list[list[float]]:
    """Generate BGE-M3 embeddings for all documents."""
    from sentence_transformers import SentenceTransformer

    print(f"Loading BGE-M3 from {model_path}...")
    model = SentenceTransformer(model_path)

    texts = [doc["content"] for doc in documents]
    print(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=16)
    return embeddings.tolist()


def seed_qdrant(
    documents: list[dict],
    embeddings: list[list[float]],
    qdrant_url: str,
    collection_name: str = "mrpl_standards",
):
    """Upload documents and embeddings to Qdrant."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
    )

    print(f"Connecting to Qdrant at {qdrant_url}...")
    client = QdrantClient(url=qdrant_url)

    vec_dim = len(embeddings[0])
    print(f"Embedding dimension: {vec_dim}")

    # Recreate collection
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
        print(f"Deleted existing collection '{collection_name}'")

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vec_dim, distance=Distance.COSINE),
    )
    print(f"Created collection '{collection_name}'")

    # Upload points
    points = []
    for i, (doc, emb) in enumerate(zip(documents, embeddings)):
        points.append(
            PointStruct(
                id=i,
                vector=emb,
                payload={
                    "doc_id": doc["doc_id"],
                    "title": doc["title"],
                    "content": doc["content"],
                    "source_file": doc["source_file"],
                    "standard_code": doc["standard_code"],
                    "chunk_index": doc["chunk_index"],
                    "indexed_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        )

    client.upsert(collection_name=collection_name, points=points)
    print(f"Uploaded {len(points)} vectors to '{collection_name}'")

    # Verify with a test search
    test_query = embeddings[0]
    results = client.query_points(
        collection_name=collection_name,
        query=test_query,
        limit=3,
    )
    print(f"\nTest search returned {len(results.points)} results:")
    for r in results.points:
        print(f"  Score: {r.score:.4f} | {r.payload['title'][:60]}...")

    return len(points)


def seed_offline(documents: list[dict], embeddings: list[list[float]], output_path: Path):
    """Save embeddings to disk for later ingestion when Qdrant is available."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "collection_name": "mrpl_standards",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "num_documents": len(documents),
        "embedding_dim": len(embeddings[0]) if embeddings else 0,
        "documents": [
            {**doc, "embedding": emb}
            for doc, emb in zip(documents, embeddings)
        ],
    }

    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2)

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"Saved {len(documents)} embedded documents to {output_path} ({size_mb:.1f} MB)")
    return len(documents)


def main():
    parser = argparse.ArgumentParser(description="Seed Qdrant with test fixtures")
    parser.add_argument("--qdrant-url", default="http://localhost:6333")
    parser.add_argument("--collection", default="mrpl_standards")
    parser.add_argument("--model-path", default="models/bge-m3")
    parser.add_argument("--fixtures-dir", default="data/test-fixtures")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Save embeddings to disk instead of uploading to Qdrant",
    )
    args = parser.parse_args()

    fixtures_dir = Path(args.fixtures_dir)
    print("=" * 60)
    print("  Sovereign Workbench — Vector DB Seeding")
    print("=" * 60)

    # Load and chunk documents
    documents = load_fixtures(fixtures_dir)
    print(f"\nLoaded {len(documents)} document chunks from {fixtures_dir}")

    # Generate embeddings
    embeddings = embed_documents(documents, args.model_path)

    if args.offline:
        output_path = Path("data/embeddings_cache.json")
        count = seed_offline(documents, embeddings, output_path)
    else:
        try:
            count = seed_qdrant(
                documents, embeddings, args.qdrant_url, args.collection
            )
        except Exception as e:
            print(f"\n⚠️  Qdrant connection failed: {e}")
            print("Falling back to offline mode...")
            output_path = Path("data/embeddings_cache.json")
            count = seed_offline(documents, embeddings, output_path)

    print(f"\n✅ Seeding complete: {count} vectors ready")


if __name__ == "__main__":
    main()
