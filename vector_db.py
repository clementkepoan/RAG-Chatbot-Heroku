import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Global vector store
pdf_vector_store = None

def initialize_vector_db(pdf_path="resources/data.pdf"):
    """
    Initialize the vector database from a PDF file using Google's embeddings.
    
    Args:
        pdf_path: Path to the PDF file to index
        
    Returns:
        FAISS vector store object
    """
    global pdf_vector_store
    
    try:
        # Check if vector store already exists
        if pdf_vector_store:
            return pdf_vector_store
            
        # Get API key from environment variable
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        print(f"Loading PDF from {pdf_path}...")
        
        # Load the PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        # Split the documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)
        
        print(f"Split PDF into {len(chunks)} chunks")
        
        # Create vector store with Google's embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=api_key
        )
        pdf_vector_store = FAISS.from_documents(chunks, embeddings)
        
        print("Vector database initialized successfully")
        return pdf_vector_store
        
    except Exception as e:
        print(f"Error initializing vector database: {e}")
        return None

def query_pdf(question, context_prefix=""):
    """
    Query the vector database with a question using Gemini.
    
    Args:
        question: User's question
        context_prefix: Additional context to prepend to the answer
        
    Returns:
        Answer from the vector database
    """
    try:
        # Initialize vector store if not already done
        vector_store = initialize_vector_db()
        if not vector_store:
            return "Sorry, I couldn't access the handbook database. Please try again later."
            
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        
        # Create a retriever
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}  # Return top 3 relevant chunks
        )
        
        # Create a custom prompt template
        template = """
        You are a helpful assistant for a club management website.
        Use the following pieces of context to answer the question at the end.
        If you don't know the answer, just say you don't know. Don't try to make up an answer.
        Act as a chatbot, so if you dont know say you dont have the data to answer the question.
        Keep the answer concise and to the point.
        
        {context}
        
        Question: {question}
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Create a chain to answer questions with Gemini
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-preview-04-17",
            google_api_key=api_key,
            temperature=0.8
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=False,
            chain_type_kwargs={"prompt": prompt}
        )
        
        # Run the chain
        result = qa_chain.invoke(question)
        
        # Format the response
        if context_prefix:
            return f"{result['result']}"
        return result['result']
        
    except Exception as e:
        print(f"Error querying vector database: {e}")
        return "Sorry, I couldn't answer your question based on the handbook. Please try asking in a different way."