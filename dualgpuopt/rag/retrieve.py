"""
RAG retrieval module for Quebec-French Legal LLM.
"""
import json
import logging
import os
from typing import Any, Dict, List

import faiss
import numpy as np

# Import sentence-transformers for embedding generation
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: sentence-transformers package not installed.")
    print("Install with: pip install sentence-transformers")
    SentenceTransformer = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class LegalRetriever:
    """Legal document retriever using FAISS."""

    def __init__(
        self,
        index_path: str,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = None,  # None = auto, 'cpu', or 'cuda:0' etc.
    ):
        """
        Initialize the retriever.

        Args:
        ----
            index_path: Path to the FAISS index file
            model_name: Name of the sentence-transformer model for embeddings
            device: Device to use for model inference ('cpu', 'cuda:0', etc.)

        """
        self.index_path = index_path
        self.model_name = model_name
        self.device = device

        # Load sentence transformer model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)

        # Load FAISS index
        logger.info(f"Loading FAISS index from {index_path}")
        self.index = faiss.read_index(index_path)

        # Load metadata
        metadata_path = f"{index_path}.meta.json"
        logger.info(f"Loading metadata from {metadata_path}")
        self.metadata = []
        with open(metadata_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    self.metadata.append(json.loads(line))

        logger.info(f"Retriever initialized with {self.index.ntotal} documents")

    def retrieve(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.1,  # Minimal threshold to filter truly unrelated results
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.

        Args:
        ----
            query: The query text
            k: Number of documents to retrieve
            threshold: Similarity threshold for filtering results

        Returns:
        -------
            List of retrieved documents with metadata and citations

        """
        # Encode query to embedding
        query_embedding = self.model.encode(query)
        # Normalize for cosine similarity
        query = np.expand_dims(query_embedding.astype("float32"), 0)
        faiss.normalize_L2(query)

        # Search the index
        distances, indices = self.index.search(query, k=k)

        # Process results
        results = []
        for _i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            # Skip if below threshold or index is invalid
            if dist < threshold or idx >= len(self.metadata) or idx < 0:
                continue

            # Get metadata for this document
            metadata = self.metadata[idx]

            # Add distance score to metadata
            metadata["score"] = float(dist)

            # Generate citation if not present
            if "citation" not in metadata:
                metadata["citation"] = self._generate_citation(metadata)

            results.append(metadata)
            
        return results

    def _generate_citation(self, metadata: Dict[str, Any]) -> str:
        """
        Generate a citation for a document based on its metadata.

        Args:
        ----
            metadata: Document metadata

        Returns:
        -------
            Citation string

        """
        # Try to extract information from metadata
        doc_id = metadata.get("id", "Unknown")
        source = metadata.get("source", "Unknown Source")

        # Format citation based on available information
        citation = f"{source} (document {doc_id})"

        # Add URL if available
        if "url" in metadata:
            citation += f", {metadata['url']}"

        return citation


def top_k(
    query: str,
    k: int = 3,
    index_path: str = "rag/qc.faiss",
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    format_citations: bool = True,
    device: str = None,
) -> List[str]:
    """
    Convenience function to retrieve top-k documents for a query.

    Args:
    ----
        query: The query text
        k: Number of documents to retrieve
        index_path: Path to the FAISS index
        model_name: Name of the sentence transformer model
        format_citations: Whether to add citation formatting
        device: Device to use for model inference ('cpu', 'cuda:0', etc.)

    Returns:
    -------
        List of document texts with citations

    """
    try:
        # Check if files exist
        if not os.path.exists(index_path):
            available_indices = [
                f for f in os.listdir(os.path.dirname(index_path)) if f.endswith(".faiss")
            ]
            logger.error(f"Index not found at {index_path}. Available indices: {available_indices}")
            return [f"Error: Index not found at {index_path}"]

        # Initialize retriever
        retriever = LegalRetriever(index_path, model_name, device=device)

        # Get results
        results = retriever.retrieve(query, k=k)

        # Format results with citations
        formatted_docs = []
        for result in results:
            text = result["text"]

            if format_citations:
                citation = result.get("citation", "Source non spécifiée")
                # Format text with citation
                formatted_text = f"{text}\n[Citation: {citation}]"
            else:
                formatted_text = text

            formatted_docs.append(formatted_text)

        return formatted_docs

    except Exception as e:
        logger.error(f"Error retrieving documents: {e}")
        return [f"Error retrieving documents: {e!s}"]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Retrieve relevant legal documents")
    parser.add_argument("query", help="Query text")
    parser.add_argument("--index", default="rag/qc.faiss", help="Path to FAISS index")
    parser.add_argument("--k", type=int, default=3, help="Number of documents to retrieve")
    parser.add_argument("--threshold", type=float, default=0.6, help="Similarity threshold")
    parser.add_argument("--no-citations", action="store_true", help="Disable citation formatting")

    args = parser.parse_args()

    docs = top_k(
        args.query,
        k=args.k,
        index_path=args.index,
        format_citations=not args.no_citations,
    )

    print(f"\nTop {len(docs)} documents for query: '{args.query}'")
    print("=" * 80)
    for i, doc in enumerate(docs):
        print(f"\n--- Document {i+1} ---")
        print(doc)
        print()
