# app.py
import streamlit as st
import requests
import uuid
import codecs
import time

# === Page Configuration ===
st.set_page_config(page_title="📄 Mario's Chat Kingdom", layout="centered")
st.title("🍄 Chat with Mario 🤖")

# === Session State Initialization ===
# A unique ID for the current chat session, used to isolate data in the backend
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
# List to store the history of messages (user and assistant)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
# List to store names of documents uploaded in the current session (for frontend display)
if "uploaded_doc_names" not in st.session_state:
    st.session_state.uploaded_doc_names = []
# Flag to track if we just reset the session
if "session_reset" not in st.session_state:
    st.session_state.session_reset = False
# Counter to force file uploader reset
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- Custom Function to Handle "End Chat" ---
def handle_end_chat():
    current_session_id = st.session_state.session_id
    
    # Send a request to the FastAPI backend to delete session-specific data from Qdrant
    try:
        with st.spinner(f"🧹 Clearing data for session '{current_session_id}' from database..."):
            response = requests.post(f"http://localhost:8000/end_session?session_id={current_session_id}")
        
        if response.status_code == 200:
            st.success(f"✅ Data for session '{current_session_id}' cleared from database. Wahoo!")
        else:
            st.error(f"❌ Failed to clear data from database: {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("❌ Mama mia! Could not connect to the backend server. Is it running? (Data might not have been cleared on backend)")
    except Exception as e:
        st.error(f"An unexpected error occurred during backend cleanup: {e}")

    # Reset frontend session state for a fresh start
    st.session_state.session_id = str(uuid.uuid4()) # Generate a completely new session ID
    st.session_state.chat_history = []              # Clear chat history
    st.session_state.uploaded_doc_names = []        # Clear the list of uploaded document names
    st.session_state.session_reset = True           # Mark that we just reset
    st.session_state.uploader_key += 1             # Change key to reset file uploader
    
    # Rerun the app to update the UI and reflect the cleared state
    st.rerun()

# === Document Upload Section ===
st.subheader("📄 Upload a Document")

# Use the uploader_key to force widget reset after session reset
uploaded_file = st.file_uploader("Upload a file to Mario's knowledge pipes!", 
                                 type=["pdf", "txt", "docx", "xlsx", "csv", "json", "html"], 
                                 key=f"file_uploader_{st.session_state.uploader_key}")

# Check if we just reset the session - if so, skip processing uploaded files this time
if st.session_state.session_reset:
    st.session_state.session_reset = False  # Reset the flag
    uploaded_file = None  # Ignore any uploaded file immediately after reset

if uploaded_file:
    # Check if this file name has already been processed in this session
    # This prevents redundant backend calls and duplicate display
    if uploaded_file.name not in st.session_state.uploaded_doc_names:
        with st.spinner(f"📄 Processing '{uploaded_file.name}'... Get ready for some power-ups!"):
            files = {
                "file": (uploaded_file.name, uploaded_file.getvalue())
            }
            data = {"session_id": st.session_state.session_id}
            try:
                upload_response = requests.post("http://localhost:8000/upload_document", files=files, data=data)
                if upload_response.status_code == 200:
                    st.success(f"✅ Document '{uploaded_file.name}' uploaded and processed. It's-a me, ready!")
                    # Add the document name to the session state for display
                    st.session_state.uploaded_doc_names.append(uploaded_file.name)
                else:
                    st.error(f"❌ Upload of '{uploaded_file.name}' failed: {upload_response.status_code}")
                    st.text(upload_response.text)
            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to the backend server. Is your Warp Pipe working (FastAPI running)?")
            except Exception as e:
                st.error(f"An unexpected error occurred during file upload: {e}")
    else:
        st.info(f"'{uploaded_file.name}' has already been collected in this session. Let's-a go!")

# Display currently uploaded documents
if st.session_state.uploaded_doc_names:
    st.markdown("---")
    st.markdown("### 📚 Mario's Knowledge Vault:")
    for doc_name in st.session_state.uploaded_doc_names:
        st.write(f"- 🌟 {doc_name}")
    st.markdown("---")

# === Chat History Display ===
# Iterates through chat_history and displays messages
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        label = "🧑‍💬 **User:**" if msg["role"] == "user" else "🍄 **Mario:**" 
        st.markdown(f"{label} {msg['content']}")

# === Sidebar for Session Management ===
with st.sidebar:
    st.markdown("### 🔁 Reset Session")
    st.write("Click below to clear all chat history and document data for this session!")
    if st.button("End Chat"):
        handle_end_chat() # Call the function to manage session reset

# === Chat Input Box (Always at the bottom) ===
question = st.chat_input("Ask Mario something...")

# === Handle User Input and Get LLM Response ===
if question:
    # Display user's question immediately
    st.chat_message("user").markdown(f"🧑‍💬 **User:** {question}")
    st.session_state.chat_history.append({"role": "user", "content": question})

    with st.chat_message("assistant"):
        with st.spinner("🤖 Mario is thinking... Wahoo!"):
            try:
                # Make a GET request to the FastAPI /chat endpoint
                response = requests.get("http://localhost:8000/chat", params={
                    "question": question,
                    "session_id": st.session_state.session_id
                }, stream=True, timeout=180) # Increased timeout for potentially longer LLM responses

                # Process the streaming response from the backend
                decoder = codecs.getincrementaldecoder("utf-8")()
                full_response = ""
                placeholder = st.empty() # Placeholder for streaming text
                for chunk in response.iter_content(chunk_size=1):
                    if chunk:
                        token = decoder.decode(chunk)
                        full_response += token
                        # Update the placeholder with the streamed text and a typing cursor
                        placeholder.markdown(f"🍄 **Mario:** {full_response}▌") 
                        time.sleep(0.02) # Small delay for typing effect

                # Display the final, complete response
                placeholder.markdown(f"🍄 **Mario:** {full_response}")
                st.session_state.chat_history.append({"role": "assistant", "content": full_response})

            except requests.exceptions.ConnectionError:
                st.error("❌ Bowser must have cut the connection! Could not connect to the backend server. Is it running?")
            except requests.exceptions.Timeout:
                st.error("⏳ Mario took too long to respond. The pipe timed out!")
            except Exception as e:
                st.error(f"An unexpected problem occurred while Mario was chatting: {e}")