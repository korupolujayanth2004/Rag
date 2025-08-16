# main.py
from fastapi import FastAPI, File, UploadFile, Form, Query
from fastapi.responses import StreamingResponse, JSONResponse
from pathlib import Path
import uuid # <<< MAKE SURE THIS LINE IS PRESENT AND AT THE TOP!

# Import backend utilities
from backend.embed_utils import embed_and_store_chunks, search_knowledge_base
from backend.document_loader import extract_text # This will use your chunker internally
from backend.chat_history import store_chat_turn, retrieve_chat_context
from backend.llm_client import stream_llm_response
from backend.session_utils import delete_session_data # For clearing session data

app = FastAPI()

# Add root endpoint to eliminate 404 errors
@app.get("/")
async def root():
    return {"message": "Mario's RAG Backend is running! 🍄", "status": "healthy", "endpoints": ["/upload_document", "/chat", "/end_session"]}

@app.post("/upload_document")
async def upload_document(file: UploadFile = File(...), session_id: str = Form("global")):
    """
    Handles document uploads, extracts text, chunks it, and embeds it into the knowledge base.
    """
    try:
        content = await file.read() # Read file content asynchronously
        filename = file.filename or "unknown.txt"
        
        # Use document_loader to extract and chunk text into Document objects
        docs = extract_text(Path(filename), content)
        
        # Embed and store the chunks (Document objects) into Qdrant
        embed_and_store_chunks(docs, session_id=session_id)
        return {"status": "✅ Document uploaded and processed. Power-up!"}
    except Exception as e:
        print(f"Error during document upload: {e}") # Log error for debugging
        return JSONResponse(status_code=500, content={"error": f"NameError: name 'uuid' is not defined" if "uuid" in str(e) else f"{type(e).__name__}: {str(e)}"})

@app.get("/chat")
async def chat(question: str, session_id: str = ""):
    """
    Chat endpoint that streams answers using chat history and knowledge base context.
    """
    # Ensure a session_id exists; create a new one if not provided (should be provided by frontend)
    if not session_id:
        session_id = str(uuid.uuid4()) # <<< 'uuid' is used here!
        print(f"Warning: No session_id provided for chat. Generated new one: {session_id}")
    
    # --- Retrieve Context ---
    # Search the knowledge base for relevant documents based on the current question and session
    kb_context = search_knowledge_base(question, session_id=session_id)
    
    # Retrieve previous chat turns for conversational context
    chat_context = retrieve_chat_context(session_id, question)
    
    # --- Construct LLM Prompt ---
    # The prompt structure guides the LLM on how to use the provided context
    prompt_for_llm = f"""
    You are Mario, a super helpful, friendly, and engaging AI assistant!
    You love to chat and make interactions fun, using Mario-esque phrases and tone.
    You're an expert at finding answers, but *only* from the knowledge you have.
    
    Here's the information I have for you:
    
    Chat History:
    {chat_context if chat_context else "No prior chat history for this session."}
    
    Knowledge Base Context:
    {kb_context if kb_context else "No relevant knowledge base context found for this question. If you want me to learn, upload a document!"}
    
    User's Question:
    {question}
    
    Please provide a helpful and friendly response, using the provided context if relevant.
    If the answer isn't in the provided context, please politely say so and encourage the user
    to provide more information or upload a document, using Mario-themed language.
    """
    
    # --- Stream LLM Response ---
    async def stream_response():
        # Determine the turn number for storing chat history
        # This calculates approximate turn number based on how many "lines" are in chat_context
        # It assumes each user/assistant turn is one line in the formatted chat_context
        turn_number = (len(chat_context.split("\n")) // 2) + 1 if chat_context else 1
        
        # Store the user's question in chat history immediately
        store_chat_turn(session_id, "user", question, turn_number)
        
        full_response = ""
        # Call the LLM client to get a streaming response
        for chunk in stream_llm_response(prompt=prompt_for_llm):
            if chunk.choices and len(chunk.choices) > 0:
                choice = chunk.choices[0]  # Get the first choice
                if hasattr(choice, 'delta') and hasattr(choice.delta, 'content') and choice.delta.content:
                    token = choice.delta.content
                    full_response += token
                    yield token # Yield each token as it arrives
        
        # Store the full assistant response in chat history once complete
        store_chat_turn(session_id, "assistant", full_response, turn_number)
    
    return StreamingResponse(stream_response(), media_type="text/plain")

@app.post("/end_session")
async def end_session(session_id: str = Query(...)):
    """
    Endpoint to explicitly clear all data (chat history and knowledge base)
    associated with a specific session_id. Called by the Streamlit frontend.
    """
    success = delete_session_data(session_id)
    if success:
        return {"status": f"✅ Session '{session_id}' and all related data deleted. See ya!"}
    else:
        return JSONResponse(status_code=500, content={"error": "❌ Failed to delete session data. Bowser's at it again!"})
