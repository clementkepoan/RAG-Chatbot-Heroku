import os
from dotenv import load_dotenv
from ai_init import query_groq_llm, query_gemini_llm
from supabase_client import search_clubs_by_interest

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def club_interest(user_question: str, provider: str = "gemini"):
    """
    If the question is about club interests, extract the interest and return matching clubs.
    Otherwise, return None.
    """
    try:
        # First, classify if the question is about club interests
        context_text = """
        You are a filter. Your task is to analyze a user question and determine if it is appropriate to query the LLM for relevant clubs based on the user's interests.

        Respond with:
        1. Yes: If the question is related to finding clubs, interests, or activities. Examples: "What clubs are available for hiking?", "Are there any photography groups?", "Can you suggest clubs for book lovers?"

        2. No: If the question is unrelated to clubs or interests, or if it is a general query not relevant to the task. Examples: "What is the weather today?", "How do I reset my password?", "Tell me a joke."

        3. No Clubs: If the question is related to clubs or interests, but there are no matching clubs in the database. Examples: "Are there any clubs for underwater basket weaving?" (assuming no such club exists).

        **STRICTLY respond with one word only:** Yes, No, or No Clubs

        Now classify the following question:
        """
        if provider.lower() == "groq":
            classification = query_groq_llm(user_question, context_text, GROQ_API_KEY)
        else:
            classification = query_gemini_llm(user_question, context_text, OPENROUTER_API_KEY)
        classification = classification.strip()
        if classification.lower() == "yes":
            # Extract interest and search for clubs
            interest = extract_interest(user_question, provider)
            if interest:
                clubs = search_clubs_by_interest(interest)
                return clubs  # Return list of clubs
            else:
                return []
        else:
            return []
    except Exception as e:
        print(f"Classification error with {provider} provider: {str(e)}")
        return []

def extract_interest(user_question: str, provider: str = "gemini") -> str:
    """
    Use LLM to extract the main interest or activity from the user's question.
    """
    prompt = """
You are an assistant that extracts the main interest or activity from a user's question about clubs.
Respond with only the interest or activity in a single word or short phrase.
Examples:
Q: I'm looking for a club about photography.
A: photography
Q: Are there any clubs for exercising?
A: exercising
Q: I want to join a music group.
A: music
Q: What clubs are available for hiking?
A: hiking

Now extract the interest from this question:
"""
    try:
        if provider.lower() == "groq":
            interest = query_groq_llm(user_question, prompt, GROQ_API_KEY)
        else:
            interest = query_gemini_llm(user_question, prompt, OPENROUTER_API_KEY)
        return interest.strip().lower()
    except Exception as e:
        print(f"Interest extraction error: {e}")
        return ""