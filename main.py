from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from classifier import classify_question, is_event_or_detail_question
from faq_formatter import (
    format_faqs_for_llm_club,
    context_website_student,
    context_website_manager,
    history_parser,
)
from ai_init import query_groq_llm, query_gemini_llm
from protection import is_question_safe
from supabase_client import save_chat_history, get_all_clubs, search_clubs_by_interest
from need_history import need_history
from club_interest import club_interest, is_general_club_list_question, extract_interest

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

        if(question.club_id) == "none":
            # General club list
                if is_general_club_list_question(question.user_question) == "yes":
                    clubs = get_all_clubs()
                    llm_response = f"Here are all of the clubs available: {', '.join([club['name'] for club in clubs])}"
                    return {
                        "answer": llm_response,
                    }
                # Club interest

                clubs = club_interest(question.user_question)
                print(f"Clubs: {clubs}")
                if clubs == "nointerest":
                    llm_response = "We couldnt really catch your interest or hobby. Please try again with a different keyword."
                    return {
                        "answer": llm_response,
                    }
                
                elif clubs == "noclubs":
                    llm_response = "Sorry, there are no clubs matching your interest. Please try a different keyword."
                    
                    return {
                        "answer": llm_response,
                    }
                elif clubs == "generalq":
                    llm_response = "Sorry, this type of question is not supported. Please ask another question."
                    
                    return {
                        "answer": llm_response,
                    }
                
                elif clubs!= "":
                    # Extract club names and create a response
                    llm_response = clubs
                    
                    return {
                        "answer": llm_response,
                    }
            
        
        

        # Step 0.5: Check if the user has a history of questions
        if need_history(question.user_question) == "Yes":
            context_text += history_parser(question.user_id, question.session_id,limit=3)


        # Step 1: Classify the question
        classification = classify_question(question.user_question)
        if not question.club_id and is_event_or_detail_question(question.user_question):
            return {
                "answer": "Please select a club first to ask about its events or details."
            }
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