# Streamlit UI
import streamlit as st
import requests
import nltk
nltk.download('punkt')

st.title("📄 RAG Mini App")

st.subheader("Upload Document")
uploaded_file = st.file_uploader("Upload a .txt file", type=["txt"])

if uploaded_file:
    content = uploaded_file.read().decode("utf-8")
    response = requests.post("http://localhost:8000/upload", files={"file": ("doc.txt", content)})
    st.success("Uploaded and processed.")

st.subheader("Ask a Question")
question = st.text_input("Enter your question")

if st.button("Get Answer") and question:
    response = requests.get("http://localhost:8000/ask", params={"question": question})
    st.markdown("**Answer:**")
    st.write(response.json()["answer"])