import os
from dotenv import load_dotenv
from ai_init import query_groq_llm, query_gemini_llm


# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def need_history(user_question: str, provider: str = "gemini") -> str:
    """
    Determine whether the chat history is needed based on the user's question.
    
    Args:
        user_question: The question text to determine
        provider: Which LLM provider to use - "openrouter" or "groq" (default: "openrouter")
        
    Returns:
        str: Classification result ('Yes' or 'No').
    """
    try:
        # Classification prompt
        context_text = """
    You are a classifier. Your task is to analyze a user question and determine if previous chat history is needed to fully understand and answer the question.

    Respond with:
    1. Yes: If the question contains pronouns (it, they, this, that, these, those) without clear referents, refers to previous topics implicitly, or seems to be a follow-up question. Examples: "Can I join it?", "When does it start?", "What about the other option?", "Is that available online?"

    2. No: If the question is self-contained and can be understood without any prior context. Examples: "What is the purpose of this club?", "How do I reset my password?", "Where can I find information about membership fees?"

    **STRICTLY respond with one word only:** Yes or No

    Now classify the following question:
    """
        
        # Choose provider based on parameter
        if provider.lower() == "groq":
            classification = query_groq_llm(user_question, context_text, GROQ_API_KEY)
        else:
            classification = query_gemini_llm(user_question, context_text, OPENROUTER_API_KEY)
        
        # Clean up response to ensure it's just the classification
        classification = classification.strip()
        
        # Validate the result
        valid_classifications = ["Yes", "No"]
        if classification not in valid_classifications:
            # If response contains unexpected content, attempt to extract correct value
            for valid in valid_classifications:
                if valid.lower() in classification.lower():
                    return valid
            # Default to "Club" if we can't determine the classification
            return "Yes"
        
        return classification
    except Exception as e:
        print(f"Classification error with {provider} provider: {str(e)}")
        # Default to Club if there's an error
        return "Yes"

#remove if this doesnt work 

def need_club_history(user_question: str, provider: str = "gemini") -> str:
    """
    Determine whether the chat history is needed based on the user's question.
    Uses LLM to classify if previous chat history is needed for context.
    Returns 'Yes' or 'No'.
    """
    try:
        context_text = """
You are a classifier. Your task is to analyze a user question and determine if previous chat history is needed to fully understand and answer the question.

Respond with:
1. Yes: If the question contains pronouns ("what about", "any others", "something else", "another one", "other options", "more clubs", "what else") without clear referents, refers to previous topics implicitly, or seems to be a follow-up question. Examples: "Can I join it?", "When does it start?", "What about the other option?", "Is that available online?"

2. No: If the question is self-contained and can be understood without any prior context. Examples: "What is the purpose of this club?", "How do I reset my password?", "Where can I find information about membership fees?"

STRICTLY respond with one word only: Yes or No

Now classify the following question:
""" + user_question

        if provider.lower() == "groq":
            classification = query_groq_llm(user_question, context_text, GROQ_API_KEY)
        else:
            classification = query_gemini_llm(user_question, context_text, OPENROUTER_API_KEY)
        
        classification = classification.strip()
        valid_classifications = ["Yes", "No"]
        for valid in valid_classifications:
            if valid.lower() in classification.lower():
                return valid
        # Default to "Yes" if unclear
        return "Yes"
    except Exception as e:
        print(f"Classification error with {provider} provider: {str(e)}")
        return "Yes"