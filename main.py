from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from classifier import classify_question
from faq_formatter import format_faqs_for_llm_club,context_website_student,context_website_manager,history_parser
from ai_init import query_groq_llm, query_gemini_llm
from protection import is_question_safe
from supabase_client import save_chat_history, drop_all_chat_history, get_last_chats, search_clubs_by_interest
from need_history import need_history
from club_interest import club_interest
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
    session_id: str

@app.post("/ask")
async def ask_question(question: Question):
    try:
        
        
        # Step 0: Check if the question is safe
        if not is_question_safe(question.user_question):
            return {
                "answer": "I'm sorry, but I cannot answer this question as it appears to be inappropriate or unrelated to club or website topics.",
            }
        
        # For Answering, enhance the context with specific instructions
        context_text = """\nIMPORTANT: Keep your answers concise and to the point. Avoid lengthy explanations.
        STRICTLY FOLLOW CONTEXT RULES!\n REFER TO PREVIOUS QUESTION AND ANSWER If the question contains pronouns (it, they, this, that, these, those) without clear referents, refers to previous topics implicitly, or seems to be a follow-up question. Examples: "Can I join it?", "When does it start?", "What about the other option?", "Is that available online?"
        """

        clubs = club_interest(question.user_question)
        if clubs:
            return {
                "answer": f"Here are some clubs related to your interest: {', '.join([club['name'] for club in clubs])}",
            "clubs": clubs
        }


        # Step 0.5: Check if the user has a history of questions
        if need_history(question.user_question) == "Yes":
            context_text += history_parser(question.user_id, question.session_id,limit=3)


        # Step 1: Classify the question
        classification = classify_question(question.user_question)
        if(classification == "Club" and question.logged_role != "clubmanager"):
        
            # Step 2: Format FAQs and get context
            context_text += format_faqs_for_llm_club(question.club_id, question.user_id)

            print(f"Context for club: {context_text}")
            
            # Step 3: Query Groq LLM
            llm_response = query_gemini_llm(question.user_question, context_text, GEMINI_API_KEY)
            #save chat history
            save_chat_history(
            question.session_id,
            question.user_id,
            question.user_question,
            llm_response
            )
            
            # Return response
            return {
                "answer": llm_response,
            }
        
        # Handle the case where the question is about the website, role student
        if(classification == "Website" and question.logged_role != "clubmanager"):
            
            # Step 2: Format FAQs and get context
            context_text += context_website_student()

            print(f"Context for Website: {context_text}")

            # Step 3: Query Groq LLM
            llm_response = query_gemini_llm(question.user_question, context_text, GEMINI_API_KEY)
            #save chat hitsory 
            save_chat_history(
            question.session_id,
            question.user_id,
            question.user_question,
            llm_response
            )
            
            # Return response
            return {
                "answer": llm_response,
            }
        
        # Handle the case where the question is about the website, role clubmanager
        if(question.logged_role == "clubmanager"):

            context_text += context_website_manager()
            llm_response = query_groq_llm(question.user_question, context_text, GROQ_API_KEY)
            print(f"Context for club manager: {context_text}")
            #save chat history
            save_chat_history(
            question.session_id,
            question.user_id,
            question.user_question,
            llm_response
            )
            return {
                "answer": llm_response,
            }
        
        # Handle the case where the question is about both website and club
        if(classification == "Both" and question.logged_role != "clubmanager"):

            context_text += format_faqs_for_llm_club(question.club_id, question.user_id) + context_website_student()
            llm_response = query_gemini_llm(question.user_question, context_text, GEMINI_API_KEY)
            
            print(f"Context for both: {context_text}")
            #save chat history
            save_chat_history(
            question.session_id,
            question.user_id,
            question.user_question,
            llm_response
            )

            return {
                "answer": llm_response,
            }
       
        # After getting llm_response:
    
        
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