# backend/chat_history.py

import os
import uuid
import time
from typing import List, Dict, Any
from backend.qdrant_client import qdrant_client, CHAT_HISTORY_COLLECTION

# Try different import approaches for qdrant-client compatibility
try:
    from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue, OrderBy
    # Try importing Order from different locations
    try:
        from qdrant_client.models import Order
    except ImportError:
        try:
            from qdrant_client.http.models import Order
        except ImportError:
            # Define Order locally if not available
            class Order:
                ASC = "asc"
                DESC = "desc"
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback for older versions
    from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue, OrderBy
    try:
        from qdrant_client.http.models import Order
    except ImportError:
        # Define Order locally if not available
        class Order:
            ASC = "asc"
            DESC = "desc"

def store_chat_turn(session_id: str, role: str, message: str, turn_number: int):
    """
    Stores a single turn of chat (user or assistant message) in Qdrant.
    """
    try:
        point_id = str(uuid.uuid4())
        timestamp = str(int(time.time()))

        payload = {
            "session_id": session_id,
            "role": role,
            "message": message,
            "turn_number": turn_number,
            "timestamp": timestamp,
        }

        qdrant_client.upsert(
            collection_name=CHAT_HISTORY_COLLECTION,
            wait=True,
            points=[
                PointStruct(id=point_id, vector=[0.0]*384, payload=payload)
            ]
        )
    except Exception as e:
        print(f"Error storing chat turn for session {session_id}: {e}")

def retrieve_chat_context(session_id: str, current_question: str, max_turns: int = 4) -> str:
    """
    Retrieves the last N turns of chat history for a given session,
    excluding the current question.
    Returns a formatted string suitable for LLM context.
    """
    try:
        session_filter = Filter(
            must=[
                FieldCondition(
                    key="session_id",
                    match=MatchValue(value=session_id)
                )
            ]
        )

        # Use scroll with order_by - try both approaches for compatibility
        try:
            scroll_result, _ = qdrant_client.scroll(
                collection_name=CHAT_HISTORY_COLLECTION,
                scroll_filter=session_filter,
                limit=max_turns * 2,
                offset=0,
                with_payload=True,
                with_vectors=False,
                order_by=OrderBy(key="turn_number", direction=Order.DESC)
            )
        except Exception:
            # Fallback for older API versions
            try:
                scroll_result, _ = qdrant_client.scroll(
                    collection_name=CHAT_HISTORY_COLLECTION,
                    scroll_filter=session_filter,
                    limit=max_turns * 2,
                    offset=0,
                    with_payload=True,
                    with_vectors=False,
                    order_by=OrderBy(key="turn_number", order=Order.DESC)
                )
            except Exception:
                # Final fallback without ordering
                scroll_result, _ = qdrant_client.scroll(
                    collection_name=CHAT_HISTORY_COLLECTION,
                    scroll_filter=session_filter,
                    limit=max_turns * 2,
                    offset=0,
                    with_payload=True,
                    with_vectors=False
                )

        chat_turns = []
        for record in scroll_result:
            if record.payload:
                chat_turns.append(record.payload)
        
        # Sort manually to ensure correct order
        chat_turns.sort(key=lambda x: x.get("turn_number", 0))

        formatted_history = []
        for turn in chat_turns:
            role = turn.get("role")
            message = turn.get("message")
            if role and message:
                formatted_history.append(f"{role.capitalize()}: {message}")
        
        return "\n".join(formatted_history)
    
    except Exception as e:
        print(f"Error retrieving chat context for session {session_id}: {e}")
        return ""