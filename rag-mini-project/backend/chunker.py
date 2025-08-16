from chonkie import RecursiveChunker
from typing import List

def chunk_text(text: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
    """
    Chunk text using Chonkie RecursiveChunker.
    """
    chunker = RecursiveChunker(
        tokenizer_or_token_counter="word",
        chunk_size=chunk_size,
        min_characters_per_chunk=10
    )
    chunks = chunker(text)
    return [chunk.text for chunk in chunks]
