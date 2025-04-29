from supabase_client import fetch_faqs_by_club, get_club_info_by_id, fetch_event_by_club,fetch_username_by_id

def format_faqs_for_llm_club(club_id,user_id):
    """
    Fetch and format club info, FAQs, and events for a given club in a format suitable for Groq LLM.

    Args:
        club_id: ID of the club to fetch FAQs, info, and events for.

    Returns:
        Formatted string with club information, FAQs, and events.
    """
    try:
        # Fetch FAQs
        faqs = fetch_faqs_by_club(club_id)
        
        # Fetch club info
        club_info = get_club_info_by_id(club_id)

        # Fetch events
        events = fetch_event_by_club(club_id)

        #fetch name
        name = fetch_username_by_id(user_id)

        # Build context
        context_text = f"Club Name: {club_info['name']}\n"
        context_text += f"Description: {club_info['description']}\n"
        context_text += f"Category: {club_info['category']}\n"
        context_text += f"Location: {club_info['location']}\n"
        context_text += f"Website: {club_info['website_url']}\n\n"
        
        context_text += """To contact the club manager, press contact club in the clubs page.\n\n"
         - Keep replies under 3 short sentences.
        """
        
        
        # Add FAQs
        if not faqs:
            context_text += "No FAQs found for this club.\n\n"
        else:
            context_text += "Frequently Asked Questions:\n\n"
            for i, faq in enumerate(faqs, 1):
                context_text += f"Q{i}: {faq['question']}\n"
                context_text += f"A{i}: {faq['answer']}\n\n"
        
        # Add events
        if not events:
            context_text += "No events found for this club.\n\n"
        else:
            context_text += "Upcoming Events:\n\n"
            for i, event in enumerate(events, 1):
                context_text += f"Event {i}:\n"
                context_text += f"  Title: {event['title']}\n"
                context_text += f"  Description: {event['description']}\n"
                context_text += f"  Location: {event['location']}\n"
                context_text += f"  Time Range: {event['time_range']}\n"
                context_text += f"  Start Date: {event['start_date']}\n"
                context_text += f"  End Date: {event['end_date']}\n"
                context_text += f"  Status: {event['status']}\n\n"

        if not name:
            context_text += "No user information found.\n\n"
        else:
            context_text += f"User Name: {name}\n\n"
        
        print(f"Formatted context for club ID '{club_id}':\n{context_text}")
        context_text += "if there is a username, greet and reply using username, for the response!.\n\n"
        # 
        return context_text
    


    except Exception as e:
        print(f"Error formatting FAQs, club info, and events for club ID '{club_id}': {e}")
        import traceback
        traceback.print_exc()
        return "Error formatting club information."
    
def context_website_student():

    context_text = """

        ----CONTEXT START----
        Website Instructions

        Account Management (Guest Access)
        - To register a new account: Click the Register button.
        - To log in to your account: Click the Login button.

        Clubs (Guest & Logged-in Access)
        - Guests can browse clubs via the Clubs tab in the navigation bar.
        - Logged-in users can view more club details and join clubs by clicking View Details.

        Events (Guest & Logged-in Access)
        - Guests and users can view upcoming events via the Events tab.
        - Only logged-in users who are members of a club can join or leave events.

        Announcements (Logged-in Only)
        - The Announcements tab displays posts and updates shared by clubs.
        - Only logged-in users can view announcements.

        Messages (Logged-in Only)
        - The Messages tab allows communication between users.
        - Available only when logged in.

        Profile & Settings (Logged-in Only)
        - To edit your profile or change your password:
        → Click the Profile icon in the top right → Select Profile.
        - To change language settings:
        → Click the Profile icon in the top right → Select Settings.

        Summary:
        - Guests can register, log in, view clubs, and browse events.
        - Logged-in users can join clubs, participate in events, view announcements, message users, and manage their profile and settings.
        ----CONTEXT END----

        STRICT MODE:
        - Keep replies under 3 short sentences.
        """

    return context_text

def context_website_manager():
    context_text ="""
----CONTEXT START----
You are a Club Manager Assistant. Use ONLY the information below.

1. Club Info
   - View & update name, banners, description, category.

2. Events
   - Add, edit, delete events (date, time, description).

3. Announcements
   - Add/edit/delete announcements.
   - Attach files (PDFs, images).
   - Delete inappropriate comments.

4. Members
   - View member list.
   - Remove members.

5. Join Requests
   - Review each request with reason.
   - Approve or decline.

6. FAQ
   - Add/edit/delete Q&As.
   - Powers the student chatbot.

----CONTEXT END----
STRICT MODE:
- Only answer using CONTEXT.
- No extra details or speculation.
- If out of scope: respond exactly:
  "Out of my scope; try logging in as a student to access the student chatbot."
- Keep replies under 3 short sentences.
"""
        
    

    return context_text
