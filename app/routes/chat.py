from fastapi import APIRouter
from pydantic import BaseModel
import os
from groq import Groq

router = APIRouter()

class ChatMessage(BaseModel):
    message: str

@router.post("/chat")
async def chat(body: ChatMessage):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        msg = "Groq API key missing. Please set GROQ_API_KEY in your environment."
        return {"response": msg, "message": msg}

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": """You are FinSight AI, a friendly financial advisor for Indian students. 
                    Give short, practical advice in simple English. 
                    Use Indian context (rupees, NSE, BSE, SIP, FD etc).
                    Max 3-4 sentences. No jargon."""
                },
                {"role": "user", "content": body.message},
            ],
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        return {"response": reply, "message": reply}
    except Exception as e:
        msg = f"Failed to generate chat response: {e}"
        return {"response": msg, "message": msg}