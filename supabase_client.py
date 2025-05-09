from supabase.client import create_client
from dotenv import load_dotenv
import os
from ai_init import query_gemini_llm, query_groq_llm

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")



# Initialize the Supabase client
def get_supabase_client():
    url = SUPABASE_URL 
    key = SUPABASE_KEY
    return create_client(url, key)

# Shared client
supabase_client = get_supabase_client()

# Fetch club name
# Fetch club info (name, description, category, location, website)
def get_club_info_by_id(club_id):
    data = supabase_client.table("clubs").select(
        "name, description, category, location, website_url,leader_name,leader_contact"
    ).eq("id", club_id).single().execute()
    
    if data.data:
        return {
            "name": data.data.get("name", "Unknown Club"),
            "description": data.data.get("description", "No description available."),
            "category": data.data.get("category", "Unknown category."),
            "location": data.data.get("location", "Unknown location."),
            "website_url": data.data.get("website_url", "No website available."),
            "leader_name": data.data.get("leader_name", "Unknown"),
            "leader_contact": data.data.get("leader_contact", "Unknown")
        }
    else:
        return {
            "name": "Unknown Club",
            "description": "No description available.",
            "category": "Unknown category.",
            "location": "Unknown location.",
            "website_url": "No website available.",
            "leader_name": "Unknown",
            "leader_contact": "Unknown"
        }
    

def get_all_clubs(formatted=True):
    data = supabase_client.table("clubs").select(
        "name, description, category"
    ).execute()
    
    if not data.data:
        return "No clubs found." if formatted else []
    
    if formatted:
        result = ""
        for club in data.data:
            result += "----------------------------------------\n"
            result += f"Club Name: {club.get('name', 'Unnamed Club')}\n"
            result += f"Description: {club.get('description', 'No description available.')}\n"
            result += f"Category: {club.get('category', 'Uncategorized')}\n"
        result += "----------------------------------------"
        return result
    else:
        return data.data


# Fetch FAQs
def fetch_faqs_by_club(club_id):
    data = supabase_client.table("club_faqs").select("*").eq("club_id", club_id).execute()
    return data.data

def fetch_event_by_club(club_id):
    """
    Fetch events for a specific club ID with only essential information.

    Args:
        club_id: The ID of the club to fetch events for.

    Returns:
        A list of events with selected fields if found, or an empty list if no events exist.
    """
    try:
        data = supabase_client.table("events").select(
            "title, description, location, time_range, start_date, end_date, status"
        ).eq("club_id", club_id).execute()
        
        if data.data:
            return data.data
        else:
            print(f"No events found for club ID: {club_id}")
            return []
    except Exception as e:
        print(f"Error fetching events for club ID '{club_id}': {e}")
        import traceback
        traceback.print_exc()
        return []

def fetch_username_by_id(user_id):
    if(user_id == "none"):
        return "Guest"
    data = supabase_client.table("profiles").select("username").eq("id", user_id).execute()
    #if username doesnt exist, return "Guest"
    return data.data


#to do context implementation 

def save_chat_history(session_id, user_id, user_question, llm_response):
    try:
        response = supabase_client.table("chat_history").insert({
            "session_id": session_id,
            "user_id": user_id if user_id != "none" else None,
            "question": user_question,
            "answer": llm_response
        }).execute()
        return response
    except Exception as e:
        print(f"Error saving chat history: {e}")
        return None


def drop_all_chat_history():
    supabase_client.table("chat_history").delete().neq("id", 0).execute()

def get_last_chats(user_id, session_id, limit=3):
    try:
        res = supabase_client.table("chat_history") \
            .select("question,answer") \
            .eq("session_id", session_id) \
            .eq("user_id", user_id if user_id != "none" else None) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        return list(reversed(res.data)) if res.data else []
    except Exception as e:
        print(f"Error retrieving chat history: {e}")
        return []

#club search for llm response

def search_clubs_by_interest(interest):
    try:
        clubs = get_all_clubs()
        
        # Process the clubs data into a structured format
        parsed_results = []
        for club in clubs:
            parsed_results.append({
                'name': club.get('name', 'Unknown'),
                'description': club.get('description', 'No description available'),
                'category': club.get('category', 'Uncategorized')
            })
        
        # Format the results into a readable string
        formatted_results = ""
        for club in parsed_results:
            formatted_results += f"Name: {club['name']}\n"
            formatted_results += f"Description: {club['description']}\n"
            formatted_results += f"Category: {club['category']}\n\n"


        context = """Match which clubs is suitable for this user interest, 
        return in this format 'Clubs matching your interest: Club A, Club B, and Club C' 
        , make sure the format is good, if no clubs match the interest, return STRICTLY 'no'
        """ + formatted_results
        user_question = f"what clubs are suitable for this {interest}"
        matched_clubs = query_gemini_llm(user_question, context, GEMINI_API_KEY)

        print(f"Matched clubs (CHECK no): {matched_clubs}")
        return matched_clubs  # <-- RETURN THIS, not formatted_results
        
    except Exception as e:
        print(f"Error searching clubs: {e}")
        return []

def get_all_clubs():
    """
    Fetch all clubs from the database.
    """
    result = supabase_client.table("clubs").select("name, description, category").execute()
    return result.data or []

