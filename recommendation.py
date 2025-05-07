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
    Extract ALL interests and hobbies as a comma-separated list. If no interests are found, respond with STRICTLY "none".
    
    Examples:
    
    Question: "I like playing sports and listening to music, what clubs do you recommend?"
    Response: sports, music
    
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
            print(f"Extracted interests: {interests}")
            return interests

        else:
            return []
    except Exception as e:
        print(f"Interest extraction error: {e}")
        return []


#this is using manual 1 by 1 searching in the supabase database but i need it to be more reliant on the LLM so can you use the reference im giving so it can query using llm input to give a more flexible answer

def match_clubs_to_interests(interests: list) -> list:
    """
    Match extracted interests to clubs in the database
    Returns a list of matched clubs with relevance scores
    """
    if not interests:
        return []
    
    # Get all clubs
    all_clubs = get_all_clubs(formatted=False)
    if not all_clubs:
        return []
    
    # Process clubs to find matches with interests
    matched_clubs = []
    
    for club in all_clubs:
        club_name = club.get('name', '').lower()
        club_description = club.get('description', '').lower()
        club_category = club.get('category', '').lower()
        
        relevance_score = 0
        matching_interests = []
        
        for interest in interests:
            interest = interest.lower()
            # Check for matches in name, description, and category
            if interest in club_name:
                relevance_score += 3
                matching_interests.append(interest)
            elif interest in club_description:
                relevance_score += 2
                matching_interests.append(interest)
            elif interest in club_category:
                relevance_score += 2
                matching_interests.append(interest)
        
        if relevance_score > 0:
            matched_clubs.append({
                'club': club,
                'score': relevance_score,
                'matching_interests': matching_interests
            })
    
    # Sort by relevance score (highest first)
    matched_clubs.sort(key=lambda x: x['score'], reverse=True)
    
    return matched_clubs

def generate_recommendations(user_question: str) -> dict:
    """
    Generate personalized club recommendations based on user question
    Returns a dict with answer and recommended clubs
    """
    # Extract interests from question
    interests = extract_interests(user_question)
    
    # If no interests found, respond accordingly
    if not interests:
        # Use LLM to ask for more specific interests
        prompt = f"""
        I couldn't identify specific interests in your question: "{user_question}"
        
        Please respond in a friendly, conversational way asking the user to share their interests or hobbies.
        Keep it brief (1-2 sentences).
        """
        response = query_gemini_llm(prompt, "", GEMINI_API_KEY)
        return {
            "answer": response,
            "clubs": [],
            "interests": []
        }
    
    # Match clubs to interests
    matched_clubs = match_clubs_to_interests(interests)
    
    # If no clubs match the interests
    if not matched_clubs:
        return {
            "answer": f"I couldn't find any clubs matching your interests in {', '.join(interests)}. Would you like to see all available clubs instead?",
            "clubs": [],
            "interests": interests
        }
    
    # Format the top 5 recommendations
    top_recommendations = matched_clubs[:5]
    club_list = [match['club'] for match in top_recommendations]
    
    # Generate personalized recommendation text with LLM
    clubs_context = ""
    for i, match in enumerate(top_recommendations, 1):
        club = match['club']
        clubs_context += f"{i}. {club['name']}: {club['description']}\n"
    
    prompt = f"""
    The user is interested in: {', '.join(interests)}
    
    Based on these interests, here are the top club recommendations:
    {clubs_context}
    
    Create a friendly, personalized response recommending these clubs to the user.
    Mention the interests you matched and why these clubs might be a good fit.
    Keep it conversational and brief (3-4 sentences maximum).
    """
    
    recommendation_text = query_gemini_llm(prompt, "", GEMINI_API_KEY)
    
    return {
        "answer": recommendation_text,
        "clubs": club_list,
        "interests": interests
    }