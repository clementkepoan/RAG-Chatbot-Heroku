import requests
import google.generativeai as genai



def query_groq_llm(user_question, context_text, groq_api_key):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }

    
    body = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": context_text},
            {"role": "user", "content": user_question}
        ],
        "temperature": 0.5
    }
    response = requests.post(url, headers=headers, json=body)
    result = response.json()
    return result['choices'][0]['message']['content']

def query_gemini_llm(user_question, context_text, gemini_api_key):
    try:
        
        
        # Configure the client with API key
        genai.configure(api_key=gemini_api_key)
        
        # Create a client instance
        client = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")
        
        # Format the prompt with system context and user question
        full_prompt = f"{context_text}\n\nUser question: {user_question}"
        
        # Generate content
        response = client.generate_content(full_prompt)
        
        # Return the text response
        return response.text
        
    except ImportError:
        # Handle case where google-generativeai package is not installed
        print("Please install the Google Generative AI package: pip install google-generativeai")
        return "Error: Google Generative AI package not installed"
    except Exception as e:
        print(f"Error querying Gemini: {str(e)}")
        return f"Error: {str(e)}"




