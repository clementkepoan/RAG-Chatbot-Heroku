import os
from dotenv import load_dotenv
from ai_init import query_gemini_llm
from supabase_client import get_all_clubs

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def extract_interests(user_question: str) -> list:
    """
    Extract interests/hobbies from user question using LLM
    Returns a list of extracted interests
    """
    prompt = """
    You are an assistant that extracts interests and hobbies from a user's question about club recommendations.
    Extract ALL interests and hobbies as a comma-separated list and classify it into these outputs [Engineering, Arts, Music, Sports, Academics, Cultural, Technology, Social]. If no interests are found or nothing is related to the output in the list, respond with "none".
    


    Examples:
    
    Question: "I like playing sports and listening to music, what clubs do you recommend?"
    Response: sports, music
    
    Qusestion: "I am interested in singing, what clubs are available?"
    Response: music

    Question: "I'm interested in photography, what clubs are available?"
    Response: photography
    
    Question: "What clubs do you recommend?"
    Response: none
    
    Extract interests from this question:
    """
    
    try:
        result = query_gemini_llm(user_question, prompt, GEMINI_API_KEY)
        if result and result.lower() != "none":
            # Convert comma-separated string to list and clean up items
            interests = [item.strip().lower() for item in result.split(',')]
            return interests
        else:
            return []
    except Exception as e:
        print(f"Interest extraction error: {e}")
        return []

def format_clubs_for_llm(clubs: list) -> str:
    """
    Formats all clubs into a readable string for LLM context.
    """
    formatted = ""
    for club in clubs:
        formatted += f"Name: {club.get('name', 'Unknown')}\n"
        formatted += f"Description: {club.get('description', 'No description available')}\n"
        formatted += f"Category: {club.get('category', 'Uncategorized')}\n\n"
    return formatted

def llm_match_clubs(interests: list, clubs_context: str) -> list:
    """
    Uses LLM to match interests to clubs and returns a list of recommended club names.
    """
    prompt = f"""
You are an assistant that matches user interests to clubs.
User interests: {', '.join(interests)}
Here is a list of clubs:

{clubs_context}

From the list above, return ONLY the club names (one per line) that best match the user's interests.
If no clubs match, respond with "none".
"""
    result = query_gemini_llm("", prompt, GEMINI_API_KEY)
    if not result or result.strip().lower() == "none":
        return []
    return [name.strip() for name in result.split('\n') if name.strip()]

def recommend_clubs(user_question: str, user_id: str, session_id: str):
    interests = extract_interests(user_question)
    if not interests:
        return {
            "status": "clarify",
            "answer": "Could you tell me about your hobbies or interests so I can recommend clubs for you?",
            "clubs": []
        }
    clubs = get_all_clubs(formatted=False)
    clubs_context = format_clubs_for_llm(clubs)
    matched_names = llm_match_clubs(interests, clubs_context)
    if matched_names:
        # Clubs found matching interest
        matched_clubs = [club for club in clubs if club['name'] in matched_names]
        return {
            "status": "matched",
            "answer": f"Based on your interests {', '.join(interests)}, I recommend these clubs: {', '.join(matched_names)}.",
            "clubs": matched_clubs
        }
    else:
        # Interest found, but no clubs match
        return {
            "status": "no_match",
            "answer": f"Sorry, I couldn't find any clubs matching your interests {', '.join(interests)}. Would you like to see all available clubs?",
            "clubs": []
        }