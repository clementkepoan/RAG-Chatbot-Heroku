from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

# Get API keys from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI()


class Question(BaseModel):
    club_id: str
    user_question: str
    user_id: str
    logged_role: str
    session_id: str


@app.post("/ask")
async def ask_question(question: Question):
    try:
        
        # Step 0: Check if the question is safe
        if not is_question_safe(question.user_question):
            return {
                "answer": "I'm sorry, but I cannot answer this question as it appears to be inappropriate or unrelated to club or website topics.",
            }
