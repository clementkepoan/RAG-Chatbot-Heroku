from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from classifier import classify_question
from faq_formatter import format_faqs_for_llm_club,context_website_student,context_website_manager
from ai_init import query_groq_llm, query_gemini_llm
from protection import is_question_safe

# Load environment variables
load_dotenv()

# Get Groq API key from environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI()

class Question(BaseModel):
    club_id: str
    user_question: str
    user_id: str
    logged_role: str

@app.post("/ask")
async def ask_question(question: Question):
    try:

        

        # Step 0: Check if the question is safe
         # Check if question is safe before processing
        if not is_question_safe(question.user_question):
            return {
                "answer": "I'm sorry, but I cannot answer this question as it appears to be inappropriate or unrelated to club or website topics.",
                #"classification": "None (Marked as unsafe)",
            }
        
        #For Answering, enhance the context with specific instructions
        context_text = """\n\nIMPORTANT: Keep your answers concise and to the point. Avoid lengthy explanations.
        STRICTLY FOLLOW CONTEXT RULES!\n\n
        """
        

        # Step 1: Classify the question
        # Handle the case where the question is about the club, role student
        classification = classify_question(question.user_question)
        if(classification == "Club" and question.logged_role != "clubmanager"):
        
            # Step 2: Format FAQs and get context
            context_text += format_faqs_for_llm_club(question.club_id, question.user_id)

            print(f"Context for club: {context_text}")
            
            # Step 3: Query Groq LLM
            #llm_response = query_groq_llm(question.user_question, context_text, GROQ_API_KEY)
            llm_response = query_gemini_llm(question.user_question, context_text, GEMINI_API_KEY)
            
            # Return response
            return {
                "answer": llm_response,
                #"classification": classification,
            }
        
        # Handle the case where the question is about the website, role student
        if(classification == "Website" and question.logged_role != "clubmanager"):
            
            # Step 2: Format FAQs and get context
            context_text += context_website_student()

            # Step 3: Query Groq LLM
            #llm_response = query_groq_llm(question.user_question, context_text, GROQ_API_KEY)
            llm_response = query_gemini_llm(question.user_question, context_text, GEMINI_API_KEY)

            # Return response
            return {
                "answer": llm_response,
                #"classification": classification,
            }
        
        # Handle the case where the question is about the website, role clubmanager
        if(question.logged_role == "clubmanager"):

            context_text += context_website_manager()
            llm_response = query_groq_llm(question.user_question, context_text, GROQ_API_KEY)
            #llm_response = query_gemini_llm(question.user_question, context_text, GEMINI_API_KEY)
            print(f"Context for club manager: {context_text}")

            return {
                "answer": llm_response,
                #"classification": classification,
            }
        
        # Handle the case where the question is about both website and club
        if(classification == "Both" and question.logged_role != "clubmanager"):

            context_text += format_faqs_for_llm_club(question.club_id, question.user_id) + context_website_student()
            #llm_response = query_groq_llm(question.user_question, context_text, GROQ_API_KEY)
            llm_response = query_gemini_llm(question.user_question, context_text, GEMINI_API_KEY)

            return {
                "answer": llm_response,
                #"classification": classification,
            }
        
            

    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Club FAQ API is running. Use POST /ask endpoint to ask questions."}

# For testing directly
if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable (Heroku sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Run with the port and host settings required for Heroku
    uvicorn.run("main:app", host="0.0.0.0", port=port)