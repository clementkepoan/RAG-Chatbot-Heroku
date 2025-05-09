import os
from dotenv import load_dotenv
from ai_init import query_groq_llm, query_gemini_llm
from faq_formatter import history_parser_recommend

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def classify_question(user_question: str, provider: str = "gemini") -> str:
    """
    Classifies a user question as 'Website', 'Club', or 'Both'.
    
    Args:
        user_question: The question text to classify
        provider: Which LLM provider to use - "openrouter" or "groq" (default: "openrouter")
        
    Returns:
        str: Classification result ('Website', 'Club', or 'Both')
    """
    try:
        # Classification prompt
        context_text = """
You are a classifier. Your task is to analyze a user question and classify its intent into one of the following three categories:

1. Website: The question is primarily about website functions or navigation. Example: "Where do I sign up online?", "How do I reset my password?", "Is there a website to join?"

2. Club: The question is only about the club's purpose, schedule, membership rules, or other non-digital aspects. Example: "What does the club do?", "When are the meetings?", "Who can join?"

3. Both: The question touches on both website operations and club details. Example: "How do I join this club?" (Joining involves both website sign-up and club-specific steps.)

**STRICTLY respond with one of the following words:** Website, Club, Both

Now classify the following question accordingly.
"""
        
        # Choose provider based on parameter
        if provider.lower() == "groq":
            classification = query_groq_llm(user_question, context_text, GROQ_API_KEY)
        else:
            classification = query_gemini_llm(user_question, context_text, OPENROUTER_API_KEY)
        
        # Clean up response to ensure it's just the classification
        classification = classification.strip()
        
        # Validate the result
        valid_classifications = ["Website", "Club", "Both"]
        if classification not in valid_classifications:
            # If response contains unexpected content, attempt to extract correct value
            for valid in valid_classifications:
                if valid.lower() in classification.lower():
                    return valid
            # Default to "Club" if we can't determine the classification
            return "Club"
        
        return classification
    except Exception as e:
        print(f"Classification error with {provider} provider: {str(e)}")
        # Default to Club if there's an error
        return "Club"
    
def classify_question_noid(user_question: str, provider: str = "gemini") -> str:
    """
    Classifies a user question 
    as :
            -Question about a single club
            -Question about what clubs are there
            -The Question is asking about club recommendation
            -General question about the University (default if unsure)
    
    Args:
        user_question: The question text to classify
        provider: Which LLM provider to use - "openrouter" or "groq" (default: "openrouter")
        
    Returns:
        str: Classification result ('single', 'clublist', 'recommendation' or  'general')
    """
    try:
        # Classification prompt
        context_text = """
You are a classifier. Your task is to analyze a user question and classify its intent into one of the following four categories:

1. Single: The question is about a specific club. Example: "Tell me about the Chess Club", "When does the Robotics Club meet?", "What does the Photography Club do?"

2. Clublist: The question is asking about what clubs are available. Example: "What clubs are there?", "Show me all the clubs", "What organizations can I join?"

3. Recommendation: The question is asking for club recommendations. Example: "What clubs would you recommend for a CS major?", "Which clubs are good for beginners?", "I'm interested in art, what clubs should I join?"

4. General: General question about the university or something else not directly related to clubs. Example: "What are the campus hours?", "Where is the library?", "How do I contact administration?"

**STRICTLY respond with one of the following words:** single, clublist, recommendation, general

Now classify the following question accordingly.
"""
        
        # Choose provider based on parameter
        if provider.lower() == "groq":
            classification = query_groq_llm(user_question, context_text, GROQ_API_KEY)
        else:
            classification = query_gemini_llm(user_question, context_text, OPENROUTER_API_KEY)
        
        # Clean up response to ensure it's just the classification
        classification = classification.strip().lower()
        
        # Validate the result
        valid_classifications = ["single", "clublist", "recommendation", "general"]
        if classification not in valid_classifications:
            # If response contains unexpected content, attempt to extract correct value
            for valid in valid_classifications:
                if valid in classification:
                    return valid
            # Default to "general" if we can't determine the classification
            return "general"
        
        return classification
    except Exception as e:
        print(f"Classification error with {provider} provider: {str(e)}")
        # Default to general if there's an error
        return "general"
    


def classify_return_recommendation(history: str) -> bool:
    RECOMMENDER_PROMPTS = [
        "Could you tell me about your hobbies or interests so I can recommend clubs for you?"
    ]
    for line in history.splitlines():
        for prompt in RECOMMENDER_PROMPTS:
            if prompt in line.strip():
                return True
    return False

def classify_return_all_clubs(history: str) -> bool:
    RECOMMENDER_PROMPTS = [
        "Would you like to see all available clubs"
    ]
    for line in history.splitlines():
        for prompt in RECOMMENDER_PROMPTS:
            if prompt in line.strip():
                return True
    return False