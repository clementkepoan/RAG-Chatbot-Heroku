from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from classifier import classify_question, classify_question_noid, classify_return_recommendation, classify_return_all_clubs
from faq_formatter import format_faqs_for_llm_club,history_parser
from ai_init import query_gemini_llm
from protection import is_question_safe
from supabase_client import save_chat_history, get_all_clubs

from vector_db import query_pdf
from recommender import recommend_clubs
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

        if question.club_id == "none":


            ##########CATCHERRRR##########
            # Fetch the latest chat history (1 or 3 entries as you prefer)
            chat_history = history_parser(question.user_id, question.session_id, limit=1)
            print(f"Chat history: {chat_history}")
            # Check for recommender triggers in history
            if classify_return_recommendation(chat_history):
                print(f"classify_return_reccomendation:)")
                # Go straight to recommendation
                result = recommend_clubs(
                    question.user_question,
                    question.user_id,
                    question.session_id
                )
                save_chat_history(
                    question.session_id,
                    question.user_id,
                    question.user_question,
                    result["answer"]
                )
                return {
                    "answer": result["answer"],
                }
            
            classify_return_all_clubs_store = classify_return_all_clubs(chat_history,question.user_question)
            

            if (classify_return_all_clubs_store == "yes"):
                

                context_text = get_all_clubs()
                context_text += "Parse this data of clubs in to a description of what clubs are there and what they do."
                llm_response = query_gemini_llm(question.user_question, context_text, GEMINI_API_KEY)
                save_chat_history(
                    question.session_id,
                    question.user_id,
                    question.user_question,
                    llm_response
                )

                return{
                    "answer": llm_response,
                    }
            
            if (classify_return_all_clubs_store == "no"):

                

                save_chat_history(
                    question.session_id,
                    question.user_id,
                    question.user_question,
                    "Alright, what else can I help you with?"
                )

                return{
                    "answer": "Alright, what else can I help you with?"
                    }
            
        
            ##########CATCHERRRR##########

            # If not triggered, continue as normal    
            # 

            history = history_parser(question.user_id, question.session_id, limit=3)
 
            history += "Current Question: " + question.user_question + "\n"
            
            classification_noid = classify_question_noid(question.user_question,prefix=history)
            print(f"Classification noid: {classification_noid}")

            if(classification_noid == "single"):

                save_chat_history(
                    question.session_id,
                    question.user_id,
                    question.user_question,
                    "To ask more question about a club please select a club from the dropdown list."
                )

                return{
                    "answer": "To ask more question about a club please select a club from the dropdown list."
                    }
            
            if(classification_noid == "clublist"):
                print(f"clublist)")
                
                context_text = get_all_clubs()
                context_text += "Parse this data of clubs in to a description of what clubs are there and what they do."
                llm_response = query_gemini_llm(question.user_question, context_text, GEMINI_API_KEY)

                save_chat_history(
                    question.session_id,
                    question.user_id,
                    question.user_question,
                    llm_response
                )


                return{
                    "answer": llm_response,
                    }


            if(classification_noid == "recommendation"):
                #print(f"Context for recommendation: {context_text}")
                print(f"reccommendation)")
                result = recommend_clubs(
                    question.user_question,
                    question.user_id,
                    question.session_id
                )
                llm_response = result["answer"]
                save_chat_history(
                    question.session_id,
                    question.user_id,
                    question.user_question,
                    result["answer"]
                )
                return {
                    "answer": result["answer"],
                    
                }

            if(classification_noid == "general"):
                print(f"general)")
                # Use the vector database implementation with Gemini
                llm_response = query_pdf(question.user_question,mode="general_club", context_prefix="")

                save_chat_history(
                    question.session_id,
                    question.user_id,
                    question.user_question,
                    llm_response
                )
                return {
                    "answer": llm_response,
                }
        






        ###############Section when the user has selected a club###############

        # For Answering, enhance the context with specific instructions
        context_text = """\n\nIMPORTANT: Keep your answers concise and to the point. Avoid lengthy explanations.
        STRICTLY FOLLOW CONTEXT RULES!\n\n 
        STRICTLY FOLLOW THIS: If the question uses vague pronouns (like "it", "they", "this", "that", etc.) or refers implicitly to something already discussed (e.g., previous messages or the current state of the club), always use the most recent Q&A to determine what the user is asking.\n\n
        Examples:\n

        "Can I join it?" → Ask: Join what? → If the previous message said "no events", then reply that there’s nothing to join right now.\n

        "When does it start?" → Check what “it” refers to in the last message.\n

        "Is that available online?" → Identify what “that” is from earlier replies.\n

        Only use FAQs directly if the current conversation clearly clarify the intent \n\n

        GREET BACK IF ITS A GREETING QUESTION OR THANK YOU QUESTION. Examples: "Thank you!", "Hi, how are you?", "Hello, can you help me?", "Thanks for your assistance!", "I appreciate your help!", "Goodbye!", "See you later!", "Take care!".\n\n
        """

        #Add history to context
        history= history_parser(question.user_id, question.session_id,limit=3)
        context_text += history


        # Step 1: Classify the question
        classification = classify_question(question.user_question,prefix=history)
        print(f"Classification: {classification}")


        if(classification == "Club" and question.logged_role != "clubmanager"):
        
            # Step 2: Format FAQs and get context
            context_text += format_faqs_for_llm_club(question.club_id, question.user_id)

            print(f"Context for club: {context_text}")
            
            # Step 3: Query Groq LLM
            llm_response = query_gemini_llm(question.user_question, context_text, GEMINI_API_KEY)
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
            print(f"history for website_student: {context_text}")
            
            # Step 2: Format FAQs and get context
            llm_response = query_pdf(question.user_question,mode="website_student", context_prefix="{context_text}")
            
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
        
        if(classification == "General" and question.logged_role != "clubmanager"):

            save_chat_history(
            question.session_id,
            question.user_id,
            question.user_question,
            "Im a club specific assistant, please select the general option from the dropdown to ask me general questions."
            )

            return{
                "answer": "Im a club specific assistant, please select the general option from the dropdown to ask me general questions."
            }
        






        ############# SEPERATE###############

        # Handle the case where the question is about the website, role clubmanager
        if(question.logged_role == "clubmanager"):

            llm_response = query_pdf(question.user_question,mode="website_manager", context_prefix="{context_text}")

            save_chat_history(
            question.session_id,
            question.user_id,
            question.user_question,
            llm_response
            )
            return {
                "answer": llm_response,
            }
        
        
    
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Club FAQ API is running. Use POST /ask endpoint to ask questions."}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}



# For testing directly
if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable (Heroku sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Run with the port and host settings required for Heroku
    uvicorn.run("main:app", host="0.0.0.0", port=port)
