# backend/qdrant_client.py

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PayloadSchemaType, FilterSelector, Filter, CollectionStatus
import os
from dotenv import load_dotenv

load_dotenv()

# === Environment Variables ===
QDRANT_HOST = os.getenv(
    "QDRANT_HOST",
    "http://localhost:6333" # Default to local if not set, or your cloud URL
)
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") # Only needed for cloud Qdrant

# === Collection Names ===
KB_COLLECTION = "rag_collection" # For document embeddings
CHAT_HISTORY_COLLECTION = "chat_history_collection" # For chat messages

# === Qdrant Client Initialization ===
qdrant_client = QdrantClient(
    url=QDRANT_HOST,
    api_key=QDRANT_API_KEY,
    prefer_grpc=False, # Set to True for gRPC, False for REST
    timeout=30, # Increased timeout for potentially slow operations
    # check_compatibility=False, # Uncomment if you face compatibility issues with Qdrant versions
)

print("✅ Connected to Qdrant via REST")

# === Collection Creation and Management ===
def ensure_collection_exists(name: str, vector_size: int = 384):
    """
    Ensures a Qdrant collection exists. If not, it creates it.
    """
    try:
        # Check if collection exists
        info = qdrant_client.get_collection(collection_name=name)
        if info.status == CollectionStatus.GREEN:
            print(f"✅ Collection exists and is ready: {name}")
            return
    except Exception:
        # Collection does not exist, so proceed to create
        pass

    print(f"🆕 Creating collection: {name}")
    qdrant_client.recreate_collection(
        collection_name=name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE) # Cosine similarity for embeddings
    )
    print(f"🎉 Collection '{name}' created successfully!")


# === Payload Indexing Helper ===
def create_index_if_needed(collection: str, field_name: str, schema_type: str):
    """
    Creates a payload index on a specified field within a collection if it doesn't already exist.
    Payload indexes speed up filtering operations (e.g., by session_id).
    """
    try:
        schema_enum = getattr(PayloadSchemaType, schema_type.upper())
        qdrant_client.create_payload_index(
            collection_name=collection,
            field_name=field_name,
            field_schema=schema_enum
        )
        print(f"🔧 Indexed '{field_name}' as {schema_type} in '{collection}'")
    except Exception as e:
        # This error often means the index already exists, which is fine.
        if "already exists" in str(e): # More specific check
            # print(f"ℹ️ Index for '{field_name}' in '{collection}' already exists.")
            pass # Suppress common "already exists" error
        else:
            print(f"⚠️ Failed to create index for '{field_name}' in '{collection}': {e}")


# === Data Cleanup Utility (for development/testing) ===
def clean_collections():
    """
    Deletes all data from both the RAG knowledge base and chat history collections.
    USE WITH CAUTION: This will wipe your data!
    """
    print("🧹 Cleaning old data from all collections...")

    # Selector to delete all points in a collection (empty Filter() means no specific filter)
    all_points_selector = FilterSelector(filter=Filter())

    try:
        qdrant_client.delete(
            collection_name=KB_COLLECTION,
            points_selector=all_points_selector
        )
        print(f"🗑️ All data cleaned from '{KB_COLLECTION}'.")

        qdrant_client.delete(
            collection_name=CHAT_HISTORY_COLLECTION,
            points_selector=all_points_selector
        )
        print(f"🗑️ All data cleaned from '{CHAT_HISTORY_COLLECTION}'.")
        print("🗑️ All old data cleaned from collections successfully.")

    except Exception as e:
        print(f"❌ Error during collection cleanup: {e}")

# === Initial Setup when this module is imported ===
# Ensure collections exist and create necessary payload indexes
ensure_collection_exists(KB_COLLECTION)
ensure_collection_exists(CHAT_HISTORY_COLLECTION)

# Create indexes for filtering and ordering chat history
create_index_if_needed(CHAT_HISTORY_COLLECTION, "session_id", "keyword")
create_index_if_needed(CHAT_HISTORY_COLLECTION, "turn_number", "integer")
create_index_if_needed(CHAT_HISTORY_COLLECTION, "timestamp", "keyword") # Useful for sorting/filtering by time

# Create indexes for filtering knowledge base documents
create_index_if_needed(KB_COLLECTION, "session_id", "keyword")
create_index_if_needed(KB_COLLECTION, "upload_timestamp", "keyword")
create_index_if_needed(KB_COLLECTION, "file_type", "keyword")
create_index_if_needed(KB_COLLECTION, "source", "keyword") # Index source if you use it for filtering

# === IMPORTANT: Wipe previous data (OPTIONAL - COMMENT OUT AFTER FIRST RUN!) ===
# This line will wipe all your data from Qdrant EVERY TIME the backend starts.
# It's useful for initial setup and debugging, but comment it out for persistence.
clean_collections()