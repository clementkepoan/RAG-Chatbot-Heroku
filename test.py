from supabase_client import get_last_chats  # Replace 'your_module_name' with your actual filename (without .py)

# Test inputs
user_id = "3db27fda-b253-4a71-81c8-c6d1d007c026"
session_id = "123"

# Call and print results
if __name__ == "__main__":
    chats = get_last_chats(user_id, session_id, limit=3)
    print("Retrieved Chat History:")
    for i, chat in enumerate(chats, 1):
        print(f"{i}. Q: {chat['question']}\n   A: {chat['answer']}\n")
