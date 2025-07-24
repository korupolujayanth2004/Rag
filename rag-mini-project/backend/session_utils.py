# backend/session_utils.py

from backend.qdrant_client import qdrant_client, KB_COLLECTION, CHAT_HISTORY_COLLECTION
# Import FilterSelector from qdrant_client.models to correctly structure delete requests
from qdrant_client.models import Filter, FieldCondition, MatchValue, FilterSelector

def delete_session_data(session_id: str) -> bool:
    """
    Deletes all data associated with a given session_id from both the knowledge base
    and chat history collections in Qdrant.
    Returns True on success, False on failure.
    """
    print(f"🗑️ Deleting session data for session_id={session_id}")

    # Define the filter to target points that belong to the specified session_id
    session_filter_condition = Filter(
        must=[
            FieldCondition(
                key="session_id", # The field in your payload storing the session ID
                match=MatchValue(value=session_id) # The value to match
            )
        ]
    )

    try:
        # Delete points from the chat history collection
        qdrant_client.delete(
            collection_name=CHAT_HISTORY_COLLECTION,
            # points_selector must be a PointsSelector object (like FilterSelector)
            points_selector=FilterSelector(filter=session_filter_condition)
        )
        print(f"🗑️ Deleted chat history for session '{session_id}'.")

        # Delete points from the knowledge base (RAG) collection
        qdrant_client.delete(
            collection_name=KB_COLLECTION,
            points_selector=FilterSelector(filter=session_filter_condition)
        )
        print(f"🗑️ Deleted knowledge base data for session '{session_id}'.")

        print(f"✅ All session data for '{session_id}' successfully deleted. Game Over (for this session)!")
        return True
    except Exception as e:
        print(f"❌ Error deleting session data for session '{session_id}': {e}")
        return False