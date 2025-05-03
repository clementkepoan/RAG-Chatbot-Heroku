from supabase.client import create_client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")



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

