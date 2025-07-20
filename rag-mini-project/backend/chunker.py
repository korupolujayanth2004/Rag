from nltk.tokenize import sent_tokenize
import nltk
import re

# Download the new punkt_tab tokenizer
try:
    nltk.download('punkt_tab')
except:
    # Fallback if punkt_tab is not available
    try:
        nltk.download('punkt')
    except:
        print("Warning: NLTK punkt tokenizer not available")

def chunk_text(text, chunk_size=200, overlap=50):
    """
    Chunk text into smaller segments with word-based overlap.
    
    Args:
        text (str): Input text to chunk
        chunk_size (int): Maximum words per chunk
        overlap (int): Number of overlapping words between chunks
    
    Returns:
        list: List of text chunks
    """
    try:
        # Try using NLTK sentence tokenizer
        sentences = sent_tokenize(text)
    except LookupError:
        # Fallback to regex-based sentence splitting if NLTK fails
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        words = sentence.split()
        word_count = len(words)

        # If adding this sentence doesn't exceed chunk size
        if current_length + word_count <= chunk_size:
            current_chunk.append(sentence)
            current_length += word_count
        else:
            # Finalize current chunk
            if current_chunk:  # Only add non-empty chunks
                chunks.append(" ".join(current_chunk))

            # Handle overlap using words, not sentences
            if overlap > 0 and current_chunk:
                # Get last 'overlap' words from the end of current chunk
                overlap_words = " ".join(current_chunk).split()[-overlap:]
                current_chunk = [" ".join(overlap_words)]
                current_length = len(overlap_words)
            else:
                current_chunk = []
                current_length = 0

            # Start new chunk with the current sentence
            current_chunk.append(sentence)
            current_length += word_count

    # Add last remaining chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

# Alternative chunking function without NLTK dependency
def chunk_text_simple(text, chunk_size=200, overlap=50):
    """
    Simple text chunking without NLTK dependency.
    
    Args:
        text (str): Input text to chunk
        chunk_size (int): Maximum words per chunk
        overlap (int): Number of overlapping words between chunks
    
    Returns:
        list: List of text chunks
    """
    words = text.split()
    chunks = []
    
    i = 0
    while i < len(words):
        # Get chunk_size words starting from position i
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        
        # Move forward by (chunk_size - overlap) words
        i += max(1, chunk_size - overlap)
    
    return chunks