from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from backend.embed_utils import process_document, get_answer
import os

app = FastAPI()

@app.post("/upload")
def upload_doc(file: UploadFile = File(...)):
    try:
        content = file.file.read().decode("utf-8")
        process_document(content)
        return {"status": "✅ Document processed and stored in vector DB."}
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="❌ File must be UTF-8 encoded plain text.")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"⚠️ Internal Server Error: {str(e)}"})

@app.get("/ask")
def ask_question(question: str):
    try:
        answer = get_answer(question)
        return {"answer": answer}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"⚠️ Failed to retrieve answer: {str(e)}"})
