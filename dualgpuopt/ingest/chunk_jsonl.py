from pathlib import Path
import json
import sys
import argparse
from typing import List, Dict, Any

def chunk_document(text: str, max_length: int = 512, overlap: int = 64) -> List[Dict[str, Any]]:
    """Split a document into overlapping chunks of approximately max_length."""
    chunks = []
    
    # Simple chunking by characters with overlap
    if len(text) <= max_length:
        return [{"text": text}]
    
    start = 0
    while start < len(text):
        end = min(start + max_length, len(text))
        
        # Try to end at a period or newline if possible
        if end < len(text):
            for i in range(end-1, max(end-100, start), -1):
                if text[i] in ['.', '\n']:
                    end = i + 1
                    break
        
        chunks.append({"text": text[start:end]})
        start = end - overlap
    
    return chunks

def process_jsonl(input_file: Path, output_file: Path, max_length: int, overlap: int) -> None:
    """Process a JSONL file and chunk its documents."""
    with output_file.open('w', encoding='utf-8') as out:
        for line in input_file.read_text(encoding='utf-8').splitlines():
            doc = json.loads(line)
            chunks = chunk_document(doc['text'], max_length, overlap)
            
            # Add metadata to chunks if present in original document
            for key in doc:
                if key != 'text':
                    for chunk in chunks:
                        chunk[key] = doc[key]
            
            # Write chunks to output file
            for chunk in chunks:
                out.write(json.dumps(chunk, ensure_ascii=False) + '\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Chunk documents in a JSONL file')
    parser.add_argument('input_file', help='Input JSONL file path')
    parser.add_argument('output_file', help='Output chunked JSONL file path')
    parser.add_argument('--max-length', type=int, default=512, 
                        help='Maximum chunk length in characters')
    parser.add_argument('--overlap', type=int, default=64,
                        help='Overlap between chunks in characters')
    
    args = parser.parse_args()
    
    process_jsonl(Path(args.input_file), Path(args.output_file), 
                 args.max_length, args.overlap)
    
    print(f"Chunking complete. Output written to {args.output_file}") 