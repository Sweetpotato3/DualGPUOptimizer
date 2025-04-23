"""
Build a FAISS index from legal corpus for RAG retrieval.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import faiss
from tqdm import tqdm

# Import sentence-transformers for embedding generation
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: sentence-transformers package not installed.")
    print("Install with: pip install sentence-transformers")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def stream_jsonl(path):
    """
    Stream JSONL file line by line to avoid loading entire file into RAM.

    Args:
    ----
        path: Path to the JSONL file

    Yields:
    ------
        Parsed JSON objects
    """
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def count_lines(file_path):
    """
    Count lines in a file without loading it into memory.

    Args:
    ----
        file_path: Path to the file

    Returns:
    -------
        Number of lines
    """
    count = 0
    with open(file_path, encoding="utf-8") as f:
        for _ in f:
            count += 1
    return count


def build_faiss_index(
    corpus_path: str,
    output_path: str,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    chunk_size: int = 1000,
    max_texts: int = None,
) -> None:
    """
    Build a FAISS index from a JSONL corpus.

    Args:
    ----
        corpus_path: Path to the JSONL corpus file
        output_path: Path to save the FAISS index
        model_name: Name of the sentence-transformer model to use
        chunk_size: Number of texts to process at once
        max_texts: Maximum number of texts to include (for testing)
    """
    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    embedding_dim = model.get_sentence_embedding_dimension()
    logger.info(f"Embedding dimension: {embedding_dim}")

    # Create a FAISS index
    logger.info("Creating FAISS index")
    index = faiss.IndexFlatIP(embedding_dim)  # Inner product index (cosine similarity)

    # Load corpus
    logger.info(f"Loading corpus from {corpus_path}")
    corpus_file = Path(corpus_path)
    if not corpus_file.exists():
        logger.error(f"Corpus file not found: {corpus_path}")
        sys.exit(1)

    # Count total number of texts for progress reporting
    logger.info("Counting total texts (this may take a moment)")
    total_texts = count_lines(corpus_path)
    if max_texts and max_texts < total_texts:
        total_texts = max_texts
    logger.info(f"Processing {total_texts} texts")

    # Process texts in chunks
    texts_processed = 0
    text_metadata = []

    # Create iterator with progress tracking
    corpus_iterator = stream_jsonl(corpus_path)
    if max_texts:
        # Limit the number of items to process
        corpus_iterator = (next(corpus_iterator) for _ in range(max_texts))

    batch_texts = []
    batch_metadata = []

    # Process in batches to limit memory usage
    for obj in tqdm(corpus_iterator, total=total_texts):
        try:
            # Truncate text if too long
            text = obj["text"][:512]  # Limit to 512 chars for embedding
            batch_texts.append(text)

            # Extract metadata to keep with the text
            metadata = {"text": text}
            for key, value in obj.items():
                if key != "text":
                    metadata[key] = value
            batch_metadata.append(metadata)

            texts_processed += 1

            # Process batch when it reaches chunk_size
            if len(batch_texts) >= chunk_size:
                # Compute embeddings for the batch
                logger.info(f"Computing embeddings for batch {texts_processed//chunk_size}")
                embeddings = model.encode(batch_texts, show_progress_bar=False)

                # Add embeddings to the index
                faiss.normalize_L2(embeddings)  # Normalize for cosine similarity
                index.add(embeddings)

                # Store metadata
                text_metadata.extend(batch_metadata)

                # Clear batch
                batch_texts = []
                batch_metadata = []

        except KeyError:
            logger.warning("Skipping line without 'text' field")
            continue

    # Process any remaining texts in the last batch
    if batch_texts:
        logger.info("Computing embeddings for final batch")
        embeddings = model.encode(batch_texts, show_progress_bar=False)
        faiss.normalize_L2(embeddings)
        index.add(embeddings)
        text_metadata.extend(batch_metadata)

    # Save the index
    logger.info(f"Saving index to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    faiss.write_index(index, output_path)

    # Save metadata alongside the index
    metadata_path = f"{output_path}.meta.json"
    logger.info(f"Saving metadata to {metadata_path}")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(text_metadata, f, ensure_ascii=False, indent=2)

    logger.info(f"Successfully built index with {len(text_metadata)} texts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build FAISS index from legal corpus")
    parser.add_argument("corpus", help="Path to the JSONL corpus file")
    parser.add_argument("output", help="Path to save the FAISS index")
    parser.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Name of the sentence-transformer model",
    )
    parser.add_argument(
        "--chunk-size", type=int, default=1000, help="Number of texts to process at once"
    )
    parser.add_argument("--max-texts", type=int, help="Maximum number of texts to include")

    args = parser.parse_args()

    build_faiss_index(
        args.corpus,
        args.output,
        args.model,
        args.chunk_size,
        args.max_texts,
    )
