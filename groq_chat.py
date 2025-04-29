import requests

def query_groq_llm(user_question, context_text, groq_api_key):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }

    enhanced_context = context_text + """\n\nIMPORTANT: Keep your answers concise and to the point. Avoid lengthy explanations.
    STRICTLY FOLLOW CONTEXT RULES!
    """
    body = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": enhanced_context},
            {"role": "user", "content": user_question}
        ],
        "temperature": 0.5
    }
    response = requests.post(url, headers=headers, json=body)
    result = response.json()
    return result['choices'][0]['message']['content']
