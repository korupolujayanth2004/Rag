# backend/qdrant_client.py

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PayloadSchemaType, FilterSelector, Filter, CollectionStatus
import os
from dotenv import load_dotenv

load_dotenv()

# === Environment Variables ===
QDRANT_HOST = os.getenv(
    "QDRANT_HOST",
    "https://9485db48-8672-469a-a917-41a4ebbfd533.us-east4-0.gcp.cloud.qdrant.io"  # Your cloud URL
)
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # Only needed for cloud Qdrant

# === Collection Names ===
KB_COLLECTION = "rag_collection"  # For document embeddings
CHAT_HISTORY_COLLECTION = "chat_history_collection"  # For chat messages

# === Qdrant Client Initialization ===
qdrant_client = QdrantClient(
    url=QDRANT_HOST,
    api_key=QDRANT_API_KEY,
    prefer_grpc=False,  # Set to True for gRPC, False for REST
    timeout=30,  # Increased timeout for potentially slow operations
    check_compatibility=False,  # Skip version check to avoid warnings
)

print("✅ Connected to Qdrant Cloud")

# === Collection Creation and Management ===
def ensure_collection_exists(name: str, vector_size: int = 384):
    """
    Guarantees that a collection exists; creates it only if it is missing.
    Uses create_collection (non-destructive) so no delete permission is needed.
    """
    try:
        qdrant_client.get_collection(collection_name=name)
        print(f"✅ Collection '{name}' already exists.")
    except Exception:
        print(f"🆕 Creating collection: {name}")
        try:
            qdrant_client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )
            print(f"🎉 Collection '{name}' created successfully!")
        except Exception as e:
            print(f"❌ Failed to create collection '{name}': {e}")

# === Payload Indexing Helper ===
def create_index_if_needed(collection: str, field_name: str, schema_type: str):
    """
    Creates a payload index on a field if it is not present already.
    """
    try:
        schema_enum = getattr(PayloadSchemaType, schema_type.upper())
        qdrant_client.create_payload_index(
            collection_name=collection,
            field_name=field_name,
            field_schema=schema_enum,
        )
        print(f"🔧 Indexed '{field_name}' as {schema_type} in '{collection}'")
    except Exception as e:
        if "already exists" in str(e):
            pass  # Index is already there – ignore
        else:
            print(f"⚠️ Could not create index '{field_name}' on '{collection}': {e}")

# === Data Cleanup Utility (for development/testing) ===
def clean_collections():
    """
    Deletes ALL points from both collections.
    Call it manually; do NOT run automatically in production.
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
create_index_if_needed(CHAT_HISTORY_COLLECTION, "timestamp", "keyword")  # Useful for sorting/filtering by time

# Create indexes for filtering knowledge base documents
create_index_if_needed(KB_COLLECTION, "session_id", "keyword")
create_index_if_needed(KB_COLLECTION, "upload_timestamp", "keyword")
create_index_if_needed(KB_COLLECTION, "file_type", "keyword")
create_index_if_needed(KB_COLLECTION, "source", "keyword")  # Index source if you use it for filtering

# === IMPORTANT: Data wipe is now commented out ===
# This line will wipe all your data from Qdrant EVERY TIME the backend starts.
# It's useful for initial setup and debugging, but comment it out for persistence.
# Uncomment ONLY when you need to clear data manually:
# clean_collections()
