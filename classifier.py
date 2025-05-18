import os
import re
from dotenv import load_dotenv
from ai_init import query_groq_llm, query_gemini_llm
from faq_formatter import format_faqs_for_llm_club

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def classify_question(user_question: str, provider: str = "gemini",prefix="") -> str:
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

        1. **Website** 
        The question is primarily about website functions or navigation.
        This includes questions about how to use the website, where to find information, or how to sign up. 
        Example: 
        - "Where do I sign up online?", 
        - "How do I reset my password?"
        - "Is there a website to join?"
        - "How do I find my profile?"
        - "How do I change my email address?"

        2. **Club** 
        The question is only about the club's purpose, schedule, membership rules, or other non-digital aspects. 
        This includes questions about club activities, events, or general information.
        Example: 
        - "What does the club do?", 
        - "When are the meetings?" 
        - "Who can join?"
        - "What are the benefits of joining?"

        3. General: General question about the university or something else not directly related to website or clubs. 
        This includes campus logistics, academic services, facilities, or administrative questions.
        Example:
        - "What is NDHU" 
        - "How do I report bugs?" 
        - "How do I contact administration?"
        - "How do i create new clubs?"

        STRICTLY FOLLOW THIS: If the question uses vague pronouns (like "it", "they", "this", "that", etc.) or refers implicitly to something already discussed (e.g., tell me more, explain more, ), you may use the conversation history provided below (If it exist).\n\n
        """

        context_text += f"{prefix}\n\n"
        
        
        context_text += """
        **STRICTLY respond with one of the following words:** Website, Club, General

        Now classify the following question accordingly.
        """

        print(f"classifier context: {context_text}")
        
        # Choose provider based on parameter
        if provider.lower() == "groq":
            classification = query_groq_llm(user_question, context_text, GROQ_API_KEY)
        else:
            classification = query_gemini_llm(user_question, context_text, GEMINI_API_KEY)
        
        # Clean up response to ensure it's just the classification
        classification = classification.strip()
        
        # Validate the result
        valid_classifications = ["Website", "Club", "General"]
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
    
def classify_question_noid(user_question: str, provider: str = "gemini",prefix="") -> str:
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
        Before you classify, please read the following instructions carefully:
        STRICTLY FOLLOW THIS: If the question uses vague pronouns (like "tell me more", "Explain more", "this", "what is this about", etc.) or refers implicitly to something already discussed (e.g., previous messages or the current state of the club), always refer back to the history (IF IT EXIST).\n\n
        """

        context_text += f"{prefix}\n\n"

        context_text += """
        1. **single**  
        The question is about a specific club.  
        This includes questions that refer to a known club name or ask about a club's activities, schedule, or members.  
        Examples:  
        - "Tell me about the Chess Club"  
        - "When does the Robotics Club meet?"  
        - "What does the Photography Club do?"  
        - "What are the benefits of joining the Debate Club?"

        2. **clublist**  
        The question is asking for a list or overview of available clubs or organizations.  
        Use this **only if** the user is clearly asking for all or most club options.  
        If the question is ambiguous or focused on a specific interest or recommendation, DO NOT use this category.  
        Examples:  
        - "What clubs are there?"  
        - "Show me all the clubs"  
        - "What organizations can I join?"  
        - "List the clubs on campus"
        
        3. **recommendation**  
        The question is asking for suggestions about what clubs to join, either directly or indirectly.  
        This includes both explicit requests for recommendations (e.g., "What do you recommend?") and implicit intent (e.g., expressing interest, indecision, or personal preferences).  
        Common phrases include: "interested in", "looking for", "what should I join", "any club for", etc.  
        Examples:  
        - "What clubs would you recommend for a CS major?"  
        - "Which clubs are good for beginners?"  
        - "I'm interested in art, what clubs should I join?"  
        - "I'm looking for something fun to join"  
        - "Any suggestions for clubs related to volunteering?"  
        - "Are there clubs for shy people?"  
        - "Is there any club I can join that helps with public speaking?"  
        - "I'm new and not sure what club to join"

        4. **general**  
        The question is about the university or about how to use the website.  
        This includes campus logistics, academic services, facilities, or administrative questions.  
        Examples:  
        - "Where is the library?"  
        - "How to report bugs?"  
        - "What can the chatbot do?"  
        - "How do I view announcments?"  
        - "What is NDHU?"
        - "How do I join clubs?"
        
        **STRICTLY respond with one of the following words:** single, clublist, recommendation, general

        Now classify the following question accordingly.
        """
        
        # Choose provider based on parameter
        if provider.lower() == "groq":
            classification = query_groq_llm(user_question, context_text, GROQ_API_KEY)
        else:
            classification = query_gemini_llm(user_question, context_text, GEMINI_API_KEY)
        
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
    

def classify_catcher_all_clubs(user_question: str, provider: str = "gemini",prefix="") -> str:
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
        str: Classification result ('yes', 'no', or  'continue')
    """
    try:
        # Classification prompt
        context_text = """
        You are a classifier. Your task is to analyze a user question and classify its intent into one of the following four categories:
        Before you classify, please read the following instructions carefully:
        STRICTLY FOLLOW THIS: If the question uses vague pronouns (like "tell me more", "Explain more", "this", "what is this about", etc.) or refers implicitly to something already discussed (e.g., previous messages or the current state of the club), always refer back to the history (IF IT EXIST).\n\n
        """

        context_text += f"{prefix}\n\n"

        context_text += """
        1. yes
        Select this category if the user clearly expresses interest in seeing the full list of available clubs.
        These responses indicate affirmation or agreement with the idea of viewing all clubs.
        This means the user is intending to say YES to "Would you like to see all available clubs"
        Examples:

        "Yes, I would like to see."

        "Show me."

        "Alright, sure."

        "That would be great."

        "Yes"

        "Okay, please show me."

        2. no
        Select this category if the user clearly declines or rejects the idea of seeing the entire list of clubs.
        They do not want to view all available clubs.
        This means the user is intending to say NO to "Would you like to see all available clubs"
        Examples:

        "No."

        "No, I don't want to see all available clubs."

        "I'm not interested in seeing the full list."

        "" (empty response)

        "List the clubs on campus" (This is a request for a filtered list, not all clubs.)

        3. continue
        Select this category for all other types of responses, especially those that express a specific interest, question, or request for recommendations, rather than a direct yes or no.
        This includes ambiguous responses or responses that explore particular club types or user preferences.

        Examples:

        "What clubs would you recommend for a CS major?"

        "Which clubs are good for beginners?"

        "I'm interested in art; what clubs should I join?"

        "Are there any volunteering clubs?"

        "Do you have clubs for shy people?"

        "I'm looking for something fun to join."

        "Is there any club to help with public speaking?"

        "I'm new and not sure what club to join."



        
        **STRICTLY respond with one of the following words:** yes, no, continue

        Now classify the following question accordingly.
        """
        
        # Choose provider based on parameter
        if provider.lower() == "groq":
            classification = query_groq_llm(user_question, context_text, GROQ_API_KEY)
        else:
            classification = query_gemini_llm(user_question, context_text, GEMINI_API_KEY)
        
        # Clean up response to ensure it's just the classification
        classification = classification.strip().lower()
        
        # Validate the result
        valid_classifications = ["yes", "no", "continue"]
        print(f"Classification catcher all clubs: {classification}")
        if classification not in valid_classifications:
            # If response contains unexpected content, attempt to extract correct value
            for valid in valid_classifications:
                if valid in classification:
                    return valid
            # Default to "general" if we can't determine the classification
            return "continue"
        
        return classification
    except Exception as e:
        print(f"Classification error with {provider} provider: {str(e)}")
        # Default to general if there's an error
        return "continue"
    

def classify_return_recommendation(history: str) -> bool:
    RECOMMENDER_PROMPTS = [
        "Could you tell me about your hobbies or interests so I can recommend clubs for you?"
    ]
    for line in history.splitlines():
        for prompt in RECOMMENDER_PROMPTS:
            if prompt in line.strip():
                return True
    return False

def classify_return_all_clubs(history: str,user_question: str = "") -> str:
    
    if user_question:

        classification = classify_catcher_all_clubs(
            user_question, 
            prefix=history
        )


    return classification


def classify_edit(user_question: str, provider: str = "gemini", prefix: str = "") -> str:
    """
    Classifies whether a user question is an edit-club intent.
    
    Args:
        user_question: The question text to classify
        provider: Which LLM provider to use - "openrouter" (Gemini) or "groq"
        prefix: Optional conversational history to include as context
        
    Returns:
        str: "Edit" if the user is asking to modify club details; otherwise "None"
    """
    try:
        # Build the instruction prompt
        prompt = f"""
        You are an intent classifier. Your task is to decide if the user is asking
        to edit existing club details (name, description, category, location, meeting_time,
        website_url, leader_name, or leader_contact).

        If the user is requesting to update any of those fields, respond with exactly:
            Edit

        If not, respond with exactly:
            None

        Conversation history (if any):
        {prefix}

        User's message:
        \"\"\"
        {user_question}
        \"\"\"
        """
        # Call the chosen LLM
        if provider.lower() == "groq":
            raw = query_groq_llm(prompt, "", GROQ_API_KEY)
        else:
            raw = query_gemini_llm(prompt, "", GEMINI_API_KEY)

        
        # Normalize
        raw = raw.strip().lower()
        

        valid_classifications = ["edit", "none"]

        if raw not in valid_classifications:
            # If response contains unexpected content, attempt to extract correct value
            for valid in valid_classifications:
                if valid in raw:
                    return valid
            # Default to "general" if we can't determine the classification
            return "none"
        return raw

    except Exception as e:
        print(f"classify_edit error ({provider}): {e}")
        return "None"

    

        
        
        
  
