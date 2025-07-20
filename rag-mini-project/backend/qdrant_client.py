from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_HOST = os.getenv(
    "QDRANT_HOST",
    "https://af4d46cf-7554-4390-a899-d26487a92023.eu-central-1-0.aws.cloud.qdrant.io"
)
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "rag_collection"

qdrant_client = QdrantClient(
    url=QDRANT_HOST,
    api_key=QDRANT_API_KEY,
    prefer_grpc=False,
    check_compatibility=False,
)

# Optional: Print connection test
print("✅ Connected to Qdrant via REST")

# Create collection if not exists
existing_collections = qdrant_client.get_collections().collections
if COLLECTION_NAME not in [col.name for col in existing_collections]:
    qdrant_client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
