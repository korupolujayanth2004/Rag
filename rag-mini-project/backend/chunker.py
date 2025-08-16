import os
from chonkie import RecursiveChunker
import nltk
from typing import List

# Ensure NLTK punkt is available and NLTK uses a writable directory (important for Spaces!)
os.environ["NLTK_DATA"] = "/tmp/nltk_data"
nltk.data.path.append("/tmp/nltk_data")
os.makedirs("/tmp/nltk_data", exist_ok=True)
nltk.download('punkt', download_dir="/tmp/nltk_data", quiet=True)

def chunk_text(text: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
    """
    Chunk text using chonkie RecursiveChunker.
    Args:
        text (str): The input text to chunk.
        chunk_size (int): Maximum number of tokens per chunk.
        overlap (int): Number of overlapping tokens between chunks (note: chonkie handles overlap differently).
    Returns:
        list: List of text chunks as strings.
    """
    # Initialize the RecursiveChunker with word-based tokenization
    chunker = RecursiveChunker(
        tokenizer_or_token_counter="word",
        chunk_size=chunk_size,
        min_characters_per_chunk=10  # Minimum characters to avoid tiny chunks
    )
    
    # Get chunks using the callable interface
    chunks = chunker(text)
    
    # Extract just the text from each chunk object
    return [chunk.text for chunk in chunks]
