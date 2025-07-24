# backend/embed_utils.py

import os
import uuid # Added for generating point IDs
import time # For upload_timestamp
from sentence_transformers import SentenceTransformer
# Qdrant client models
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue, Distance, VectorParams, NamedVector, ScrollResult
from backend.qdrant_client import qdrant_client, KB_COLLECTION # Import Qdrant client and collection name
from backend.document_loader import Document # Import the Document class definition
from typing import List

# === Embedding Model Initialization ===
# 'all-MiniLM-L6-v2' is a good balance of size and performance for many applications.
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Embedding model loaded: all-MiniLM-L6-v2")

# === Helper function to get embedding for text ===
def get_embedding(text: str) -> List[float]:
    """
    Generates an embedding (vector representation) for a given text string.
    """
    return embedding_model.encode(text).tolist()

# === Embed and Store Document Chunks ===
def embed_and_store_chunks(documents: List[Document], session_id: str):
    """
    Takes a list of Document objects, generates embeddings for their text content,
    and stores them as points in the Qdrant knowledge base collection.
    Each chunk is associated with a session_id.
    """
    points = []
    current_timestamp = str(int(time.time())) # Use a Unix timestamp for when the document was uploaded

    for doc in documents:
        # Generate embedding for the chunk's text content
        embedding = get_embedding(doc.text)

        # Create payload for Qdrant, including chunk details and session ID
        payload = {
            "chunk_id": doc.chunk_id,
            "text": doc.text,
            "metadata": doc.metadata, # Preserve original metadata from document_loader
            "session_id": session_id, # CRUCIAL: Associate each chunk with the current session
            "upload_timestamp": current_timestamp,
            "file_type": doc.metadata.get("file_type", "unknown"), # Get file_type from metadata
            "source": doc.metadata.get("source", "unknown") # Get source from metadata
        }

        points.append(
            PointStruct(
                id=str(uuid.uuid4()), # Assign a unique ID for each Qdrant point
                vector=embedding,
                payload=payload
            )
        )
    
    # Perform the upsert operation to Qdrant if there are points to store
    if points:
        qdrant_client.upsert(
            collection_name=KB_COLLECTION,
            wait=True, # Wait for the operation to complete
            points=points
        )
        print(f"Stored {len(points)} chunks for session '{session_id}' into '{KB_COLLECTION}'.")
    else:
        print("No chunks generated or provided to store.")

# === Search Knowledge Base ===
def search_knowledge_base(query_text: str, session_id: str, top_k: int = 5) -> str:
    """
    Searches the knowledge base (Qdrant) for relevant document chunks
    based on the query text and the specific session ID.
    Returns a concatenated string of the most relevant text chunks.
    """
    if not query_text.strip():
        return "" # Return empty string if query is empty

    query_embedding = get_embedding(query_text)

    # Construct a filter to ensure we only search within the current session's data
    session_filter = Filter(
        must=[
            FieldCondition(
                key="session_id",
                match=MatchValue(value=session_id)
            )
        ]
    )

    try:
        # Perform the search in Qdrant with the query vector and session filter
        search_result: List[ScrollResult] = qdrant_client.search(
            collection_name=KB_COLLECTION,
            query_vector=query_embedding,
            query_filter=session_filter, # Apply the session-specific filter
            limit=top_k, # Number of top results to retrieve
            with_payload=True # Ensure payload (text and metadata) is returned
        )

        context_chunks = []
        for hit in search_result:
            # Extract the text content from the payload of each relevant hit
            if hit.payload and 'text' in hit.payload:
                context_chunks.append(hit.payload['text'])
            # print(f"  Hit: {hit.payload.get('text', '')[:50]}... (Score: {hit.score})") # Debugging line

        if context_chunks:
            # Join relevant chunks into a single string to provide to the LLM
            return "\n\n".join(context_chunks)
        else:
            print(f"No relevant context found in KB for session '{session_id}' and query: '{query_text}'")
            return "" # No relevant context found for this session
    except Exception as e:
        print(f"Error during knowledge base search for session '{session_id}': {e}")
        return "" # Return empty string on error