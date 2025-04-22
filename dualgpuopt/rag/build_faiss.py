"""
Build a FAISS index from legal corpus for RAG retrieval.
"""
import faiss
import json
import sys
import os
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def build_faiss_index(
    corpus_path: str,
    output_path: str,
    model_name: str = 'sentence-transformers/all-MiniLM-L6-v2',
    chunk_size: int = 1000,
    max_texts: int = None
) -> None:
    """
    Build a FAISS index from a JSONL corpus.
    
    Args:
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
    
    # Load all lines from the JSONL file
    with open(corpus_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Limit number of texts if specified
    if max_texts:
        lines = lines[:max_texts]
    
    total_texts = len(lines)
    logger.info(f"Processing {total_texts} texts")
    
    # Process texts in chunks
    texts = []
    text_metadata = []
    
    for i in tqdm(range(0, total_texts, chunk_size)):
        chunk_lines = lines[i:min(i+chunk_size, total_texts)]
        chunk_texts = []
        chunk_metadata = []
        
        # Parse JSON and extract text
        for line in chunk_lines:
            try:
                obj = json.loads(line)
                # Truncate text if too long
                text = obj['text'][:512]  # Limit to 512 chars for embedding
                chunk_texts.append(text)
                
                # Extract metadata to keep with the text
                metadata = {'text': text}
                for key, value in obj.items():
                    if key != 'text':
                        metadata[key] = value
                chunk_metadata.append(metadata)
                
            except json.JSONDecodeError:
                logger.warning(f"Skipping invalid JSON line: {line[:50]}...")
                continue
            except KeyError:
                logger.warning(f"Skipping line without 'text' field")
                continue
        
        # Compute embeddings for the chunk
        logger.info(f"Computing embeddings for chunk {i//chunk_size + 1}/{(total_texts-1)//chunk_size + 1}")
        embeddings = model.encode(chunk_texts, show_progress_bar=False)
        
        # Add embeddings to the index
        faiss.normalize_L2(embeddings)  # Normalize for cosine similarity
        index.add(embeddings)
        
        # Store text and metadata
        texts.extend(chunk_texts)
        text_metadata.extend(chunk_metadata)
    
    # Save the index
    logger.info(f"Saving index to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    faiss.write_index(index, output_path)
    
    # Save metadata alongside the index
    metadata_path = f"{output_path}.meta.json"
    logger.info(f"Saving metadata to {metadata_path}")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(text_metadata, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Successfully built index with {len(texts)} texts")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build FAISS index from legal corpus")
    parser.add_argument('corpus', help='Path to the JSONL corpus file')
    parser.add_argument('output', help='Path to save the FAISS index')
    parser.add_argument('--model', default='sentence-transformers/all-MiniLM-L6-v2',
                       help='Name of the sentence-transformer model')
    parser.add_argument('--chunk-size', type=int, default=1000,
                       help='Number of texts to process at once')
    parser.add_argument('--max-texts', type=int, help='Maximum number of texts to include')
    
    args = parser.parse_args()
    
    build_faiss_index(
        args.corpus,
        args.output,
        args.model,
        args.chunk_size,
        args.max_texts
    ) 