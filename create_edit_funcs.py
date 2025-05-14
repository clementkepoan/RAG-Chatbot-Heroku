from supabase_client import save_state, clear_state, edit_clubs_by_id, load_state
from ai_init import query_gemini_llm
from cleaner import parse_llm_json_response
from classifier import classify_edit
from faq_formatter import history_parser

def handle_club_edit(question, state, gemini_api_key):
    """
    Handle club editing functionality for club managers.
    
    Args:
        question: The Question object containing user input and metadata
        state: The current state from the database for this session/user
        gemini_api_key: API key for Gemini LLM
        
    Returns:
        dict: Response with answer and any other required fields
        None: If the input doesn't match an editing operation
    """
    # Get chat history for context
    history = history_parser(question.user_id, question.session_id, limit=3)
    
    # Check if starting a new edit flow
    intent = classify_edit(question.user_question, prefix=history)
    
    # Start new editing session
    if intent == "edit" and (not state or state.get("action") != "editing"):
        save_state(
            question.session_id,
            question.user_id,
            action="editing",
            club_id=question.club_id,
            updates={}
        )
        return {
            "answer": (
                "Sure—what would you like to change? "
                "You can say things like “Change the name to X” or “Update meeting_time to Tuesdays at 5pm.”"
            )
        }

    # Handle in-progress editing
    if state and state.get("action") == "editing":
        existing = state.get("updates", {}) or {}

        # Handle completion
        if "done" in question.user_question.lower():
            result = edit_clubs_by_id(state["club_id"], **existing)
            clear_state(question.session_id, question.user_id)
            if result and result.data:
                fields = ", ".join(existing.keys())
                return {"answer": f"All set! Updated fields: {fields}. Please refresh your page to see the changes."}
            else:
                return {"answer": "Oops—couldn't save your updates. Please try again"}

        # Extract new updates from user input
        prompt = f"""
        We are updating club ID {state['club_id']}. Current pending updates:
        {existing}

        Manager says:
        \"\"\"
        {question.user_question}
        \"\"\"

        Extract any of these fields (if mentioned): 
        name, description, category, location, meeting_time, website_url, leader_name, leader_contact.
        Return a pure JSON object of only the newly specified field:value pairs.
        """
        raw = query_gemini_llm(prompt, "", gemini_api_key)
        print(f"Raw LLM response: {raw}")
        
        try:
            new_updates = parse_llm_json_response(raw)
        except ValueError:
            return {
                "answer": (
                    "Sorry, I couldn’t parse your update. "
                    "Please mention something like “set the description to …” or “update the leader_contact.”"
                )
            }

        if not new_updates:
            return {
                "answer": (
                    "I didn't catch any valid fields to update. "
                    "Please mention at least one of: name, description, category, location, "
                    "meeting_time, website_url, leader_name, leader_contact, and its new value"
                )
            }

        # Merge and save updates
        merged = {**existing, **new_updates}
        save_state(
            question.session_id,
            question.user_id,
            action="editing",
            club_id=state["club_id"],
            updates=merged
        )

        # Auto-save if all fields are filled or continue collecting updates
        if len(merged) == 7:
            result = edit_clubs_by_id(state["club_id"], **merged)
            clear_state(question.session_id, question.user_id)
            if result and result.data:
                fields = ", ".join(merged.keys())
                return {"answer": f"All set! Updated fields: {fields}."}
            else:
                return {"answer": "Oops—couldn't save your updates. Please try again."}
        else:
            fields = ", ".join(merged.keys())
            return {
                "answer": (
                    f"Got it. I'll update: {fields}. "
                    "Anything else? Say 'done' when you're finished."
                )
            }
    
    # If we reach here, we're not in an editing state
    return None