import os
from dotenv import load_dotenv
from ai_init import query_groq_llm, query_gemini_llm
from supabase_client import search_clubs_by_interest
import logging as console

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
        # Classify if the question is about club interests
        context_text = """
        You are a filter. Your task is to analyze a user question and determine if it is appropriate to query the database for relevant clubs based on the user's interests.

        Respond with:
        1. Yes: If the question is related to finding clubs based on interests,hobbies, or activities. For example, "Are there any clubs for photography?", "I want to join a sports club", "What clubs are available for music?".
        2. No: If the question is unrelated to clubs or interests, or if it is a general query not relevant to the task.

        STRICTLY respond with one word only: Yes or No

        Now classify the following question:
        """
        if provider.lower() == "groq":
            classification = query_groq_llm(user_question, context_text, GROQ_API_KEY)
        else:
            classification = query_gemini_llm(user_question, context_text, OPENROUTER_API_KEY)
        classification = classification.strip().lower()
        print (f"Classification result: {classification}")
        if classification != "no":
            # Extract interest and search for clubs
            interest = extract_interest(user_question, provider)
            if interest != "no":
                clubs = search_clubs_by_interest(interest)
                if clubs != "no":
                    return clubs  # Only return real clubs
                else:
                    return "noclubs"#return ketika gaada club yg matching
            else:
                return "nointerest" #return ketika questionnya gaada interest
        else:
            return "generalq" # return ketika question general
    except Exception as e:
        print(f"Classification error with {provider} provider: {str(e)}")
        return None

def extract_interest(user_question: str, provider: str = "gemini") -> str:
    """
    Use LLM to extract the main interest or activity from the user's question.
    If no clear interest is found, return "no interest".
    """
    prompt = """
You are an assistant that extracts the main interest or activity from a user's question about clubs.
Respond with only the interest or activity in a single word or short phrase.

Examples:
Q: I'm looking for a club about photography.
A: photography
Q: Are there any clubs for exercising?
A: sport
Q: I want to join a music group.
A: arts
Q: What clubs are available for hiking?
A: sport

if there is no interest in the question, respond STRICTLY with: 'no'
Now extract the interest from this question:
"""

    try:
        if provider.lower() == "groq":
            interest = query_groq_llm(user_question, prompt, GROQ_API_KEY)
        else:
            interest = query_gemini_llm(user_question, prompt, OPENROUTER_API_KEY)

        interest = interest.strip().lower()

        # Post-check: catch empty or generic answers
        if not interest or interest in {"none", "no", "no interest", "n/a", "?"}:
            return "no interest"
        return interest

    except Exception as e:
        print(f"Interest extraction error: {e}")
        return "no interest"
    
def is_general_club_list_question(user_question: str, provider: str = "gemini"):
    """
    Returns 'yes' only if the question is about listing ALL clubs, not about a specific interest.
    """
    context_text = """
You are a classifier. Your task is to analyze a user question and determine if it is asking for a list of ALL clubs, not clubs of a specific type or interest.

Respond with:
1. Yes: Only if the question is about listing all clubs, such as "What clubs are available?", "List all clubs", "Show me all clubs".
2. No: If the question is about clubs for a specific interest, activity, or category, such as "I want to join a sports club", "Are there any music clubs?", "Show me clubs for photography".

STRICTLY respond with one word only: Yes or No

Now classify the following question:
""" + user_question
    try:
        if provider.lower() == "groq":
            classification = query_groq_llm(user_question, context_text, GROQ_API_KEY)
            print(f"Classification result from GROQ: {classification}")
        else:
            classification = query_gemini_llm(user_question, context_text, OPENROUTER_API_KEY)
            print(f"Classification result from Gemini: {classification}")
        classification = classification.strip().lower()
        return classification
    except Exception as e:
        print(f"Classification error with {provider} provider: {str(e)}")
        return "error"