# backend/chunker.py
from chonkie import RecursiveChunker
import nltk
from typing import List # <<< ADD THIS IMPORT

# Ensure punkt is available in case fallback is needed elsewhere
nltk.download('punkt', quiet=True)

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