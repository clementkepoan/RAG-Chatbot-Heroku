from supabase_client import fetch_faqs_by_club, get_club_info_by_id, fetch_event_by_club,fetch_username_by_id, get_last_chats, search_clubs_by_interest

def format_faqs_for_llm_club(club_id, user_id):
    """
    Fetch and format club info, FAQs, and events for a given club in a format suitable for Groq LLM.

    Args:
        club_id: ID of the club to fetch FAQs, info, and events for.
        user_id: ID of the user making the request.

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

        # Fetch user name
        name = fetch_username_by_id(user_id)

        # Build context with consistent formatting
        context_text = """
        ----CONTEXT START----
        You are a Club Information Assistant. Use ONLY the information below.
        If the question is about another club, respond with: please select another club from the list, to query about other clubs.

        CLUB DETAILS:
        """
        context_text += f"- Club Name: {club_info['name']}\n"
        context_text += f"- Description: {club_info['description']}\n"
        context_text += f"- Category: {club_info['category']}\n"
        context_text += f"- Location: {club_info['location']}\n"
        context_text += f"- Website: {club_info['website_url']}\n"
        context_text += f"- Club Leader: {club_info['leader_name']}\n"
        context_text += f"- Club Leader Contact: {club_info['leader_contact']}\n"
        
        # Add FAQs
        context_text += "FREQUENTLY ASKED QUESTIONS:\n"
        if not faqs:
            context_text += "- No FAQs available for this club.\n"
        else:
            for i, faq in enumerate(faqs, 1):
                context_text += f"Q{i}: {faq['question']}\n"
                context_text += f"A{i}: {faq['answer']}\n"
        
        # Add events
        context_text += "UPCOMING EVENTS:\n"
        if not events:
            context_text += "- No upcoming events scheduled for this club.\n"
        else:
            for i, event in enumerate(events, 1):
                context_text += f"Event {i}:\n"
                context_text += f"- Title: {event['title']}\n"
                context_text += f"- Description: {event['description']}\n"
                context_text += f"- Location: {event['location']}\n"
                context_text += f"- Time Range: {event['time_range']}\n"
                context_text += f"- Start Date: {event['start_date']}\n"
                context_text += f"- End Date: {event['end_date']}\n"
                context_text += f"- Status: {event['status']}\n"

        # Add user information for personalization
        if name:
            context_text += f"USER INFORMATION:\n- Username: {name}\n"
        
        context_text += "ADDITIONAL NOTES:\n"
        context_text += "- To contact the club manager, press contact club in the clubs page.\n"
        
        context_text += "----CONTEXT END----\n"
        
        # Add strict mode instruction like other contexts
        context_text += """STRICT MODE:
        - Greet the user by name if available.
        - Only answer using the information provided in the context.
        - Keep replies under 3 short sentences.
        - Do not make up information not found in the context.
        """

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
        - If out of context scope: respond exactly:
        "Out of my scope; try logging in as a student to access the student chatbot."
        - Keep replies under 3 short sentences.
        """        
        
    return context_text

def history_parser(user_id, session_id, limit=3):
    """
    Parse the chat history of a user session to extract previous conversations.

    Args:
        user_id: ID of the user.
        session_id: ID of the session.
        limit: Number of most recent chat entries to retrieve (default: 3).

    Returns:
        A string containing the formatted chat history.
    """
    try:
        # Fetch user chat history
        chat_history = get_last_chats(user_id, session_id, limit)
        
        # Format the chat history
        formatted_history = "PREVIOUS CONVERSATION:\n"
        if not chat_history:
            formatted_history += "No previous conversation found.\n"
        else:
            for i, entry in enumerate(chat_history, 1):
                formatted_history += f"User: {entry['question']}\n"
                formatted_history += f"Assistant: {entry['answer']}\n"
        
        return formatted_history
    
    except Exception as e:
        print(f"Error parsing chat history for user ID '{user_id}': {e}")
        import traceback
        traceback.print_exc()
        return "Error retrieving conversation history."
    

    