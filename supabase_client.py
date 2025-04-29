from supabase.client import create_client, Client

# Initialize the Supabase client
def get_supabase_client():
    url = "https://semkrbcujuhqfcmgfedh.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNlbWtyYmN1anVocWZjbWdmZWRoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQyMjQ2NDAsImV4cCI6MjA1OTgwMDY0MH0.uiDe1QRsxbRsNMwvx3p0mdYWUrgtN04p0F22VOxpsv8"
    return create_client(url, key)

# Shared client
supabase_client = get_supabase_client()

# Fetch club name
# Fetch club info (name, description, category, location, website)
def get_club_info_by_id(club_id):
    data = supabase_client.table("clubs").select(
        "name, description, category, location, website_url"
    ).eq("id", club_id).single().execute()
    
    if data.data:
        return {
            "name": data.data.get("name", "Unknown Club"),
            "description": data.data.get("description", "No description available."),
            "category": data.data.get("category", "Unknown category."),
            "location": data.data.get("location", "Unknown location."),
            "website_url": data.data.get("website_url", "No website available.")
        }
    else:
        return {
            "name": "Unknown Club",
            "description": "No description available.",
            "category": "Unknown category.",
            "location": "Unknown location.",
            "website_url": "No website available."
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
    data = supabase_client.table("profiles").select("username").eq("id", user_id).execute()
    return data.data