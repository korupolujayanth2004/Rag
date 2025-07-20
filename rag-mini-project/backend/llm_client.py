from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model_name = os.getenv("OPENROUTER_MODEL", "sarvamai/sarvam-m:free")

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

def query_llm(prompt: str, context: str = "") -> str:
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{prompt}"}
        ]
    )
    return response.choices[0].message.content