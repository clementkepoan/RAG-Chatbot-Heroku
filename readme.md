# NDHU Club Chatbot System

This project is an AI-powered FAQ and club recommendation chatbot for National Dong Hwa University (NDHU). It helps students and club managers interact with club information, get recommendations, and manage club data through a conversational interface.

---

## Features

- **Natural Language Classification:** Classifies user questions as club-related, website-related, or general university queries using LLMs (Gemini, Groq).
- **Club Recommendation:** Suggests clubs based on user interests and chat history.
- **FAQ Retrieval:** Answers club-specific and website-related questions using vector search over indexed PDFs and Supabase data.
- **Club Management:** Allows club managers to edit club details via chat.
- **Context Awareness:** Maintains conversation history for context-sensitive responses.
- **Safety Filtering:** Screens user questions for safety and relevance.
- **Persistent State:** Uses Supabase for chat history, club data, and session state.
- **FastAPI Backend:** Provides a REST API for chatbot interaction.
- **Azure & Docker Ready:** Includes deployment scripts for Azure and Docker.

---

## Project Structure

```
.
├── ai_init.py              # LLM API integration (Gemini, Groq)
├── classifier.py           # Intent and question classification logic
├── cleaner.py              # LLM JSON response cleaning
├── create_edit_funcs.py    # Club editing workflow for managers
├── faq_formatter.py        # Formats club FAQs and context for LLMs
├── main.py                 # FastAPI app entry point
├── need_history.py         # Determines if chat history is needed
├── protection.py           # Safety filter for user questions
├── recommender.py          # Club recommendation logic
├── supabase_client.py      # Supabase DB integration
├── vector_db.py            # PDF vector search with ChromaDB & Gemini
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker build instructions
├── .env                    # Environment variables (not committed)
├── .github/workflows/      # GitHub Actions CI/CD
├── resources/              # PDF and docx resources
├── chroma_db/              # ChromaDB persistent storage
├── test/                   # Pytest-based integration and unit tests
└── readme.md               # This file
```

---

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/clementkepoan/RAG-Chatbot-Render.git
   cd RAG-Chatbot-Render
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   - Copy `.env.example` to `.env` and fill in your API keys and Supabase credentials.

4. **Run the API locally:**
   ```bash
   uvicorn main:app --reload
   ```

5. **Run tests:**
   ```bash
   pytest test/
   ```

---

## API Usage

- **POST `/ask`**  
  Send a JSON payload:
  ```json
  {
    "club_id": "none",
    "user_question": "What clubs do you recommend?",
    "user_id": "user-123",
    "logged_role": "student",
    "session_id": "sess-456"
  }
  ```
  **Response:**
  ```json
  {
    "answer": "Based on your interests, I recommend these clubs: ..."
  }
  ```

- **GET `/`**  
  Health check endpoint.

---

## Deployment

- **Docker:**  
  ```bash
  docker build -t clubchatbot .
  docker run -p 8000:8000 --env-file .env clubchatbot
  ```

- **Azure:**  
  See `.github/workflows/main_clubchatbot.yml` for CI/CD pipeline.

---

## Notes

- **LLM Providers:** Supports Gemini and Groq (see `.env` for API keys).
- **PDF Knowledge Base:** Place club and website handbooks in `resources/` as PDFs.
- **Supabase:** Used for persistent storage of clubs, FAQs, events, and chat state.
- **ChromaDB:** Used for vector search over PDF content.

---

## License

MIT License

---

## Acknowledgements

- [Google Generative AI](https://ai.google.dev/)
- [Groq LLM API](https://groq.com/)
- [Supabase](https://supabase.com/)
- [ChromaDB](https://www.trychroma.com/)
