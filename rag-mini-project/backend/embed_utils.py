# backend/embed_utils.py

from sentence_transformers import SentenceTransformer
from backend.qdrant_client import qdrant_client, COLLECTION_NAME
from qdrant_client.http.models import PointStruct
from backend.chunker import chunk_text
from backend.llm_client import query_llm
import uuid

model = SentenceTransformer("all-MiniLM-L6-v2")

def process_document(text):
    chunks = chunk_text(text)
    vectors = model.encode(chunks)
    points = [
        PointStruct(id=str(uuid.uuid4()), vector=vec.tolist(), payload={"text": chunk})
        for chunk, vec in zip(chunks, vectors)
    ]
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)

def get_answer(question):
    q_vector = model.encode([question])[0].tolist()
    hits = qdrant_client.search(collection_name=COLLECTION_NAME, query_vector=q_vector, limit=3)
    context = "\n".join(hit.payload["text"] for hit in hits)
    return query_llm(prompt=question, context=context)
