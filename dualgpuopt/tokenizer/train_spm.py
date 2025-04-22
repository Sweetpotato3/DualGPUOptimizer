import sentencepiece as spm
import sys
import pathlib
import json

def train_tokenizer(corpus_path, model_prefix, vocab_size=48000):
    """
    Train a SentencePiece tokenizer on a legal corpus.
    
    Args:
        corpus_path: Path to the JSONL corpus file
        model_prefix: Output model name prefix
        vocab_size: Size of the vocabulary
    """
    # Extract text from JSONL and write to a temporary file
    texts = pathlib.Path('tmp_corpus.txt')
    with texts.open('w', encoding='utf-8') as fh:
        for line in pathlib.Path(corpus_path).read_text(encoding='utf-8').splitlines():
            try:
                fh.write(json.loads(line)['text'] + '\n')
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error processing line: {e}")
    
    # Train the tokenizer
    spm.SentencePieceTrainer.train(
        input=str(texts),
        model_prefix=model_prefix,
        vocab_size=vocab_size,
        character_coverage=0.9995,
        model_type='bpe',
        user_defined_symbols=['<art>', '<al>']  # Legal article markers
    )
    
    print(f"Tokenizer trained successfully: {model_prefix}.model and {model_prefix}.vocab")
    
    # Clean up
    texts.unlink()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python train_spm.py <jsonl_corpus> <model_prefix> [vocab_size]")
        sys.exit(1)
    
    corpus = sys.argv[1]
    model_prefix = sys.argv[2]
    vocab_size = int(sys.argv[3]) if len(sys.argv) > 3 else 48000
    
    train_tokenizer(corpus, model_prefix, vocab_size) 