import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain_chroma import Chroma
import chromadb
from dotenv import load_dotenv
import shutil

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Set up ChromaDB directory
CHROMA_DB_DIR = "chroma_db"

# Initialize ChromaDB client
os.makedirs(CHROMA_DB_DIR, exist_ok=True)
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# Global vector store references (for caching)
pdf_vector_store_general_club = None
pdf_vector_website_manager = None
pdf_vector_website_student = None


def initialize_vector_db(pdf_path, mode):
    """
    Initialize the vector database from a PDF file using ChromaDB with Google's embeddings.
    
    Args:
        pdf_path: Path to the PDF file to index
        mode: Which mode/vector store to use
        
    Returns:
        ChromaDB vector store object
    """
    global pdf_vector_store_general_club
    global pdf_vector_website_manager
    global pdf_vector_website_student
    
    try:
        # Check if the specific vector store for this mode already exists in memory
        if mode == "general_club" and pdf_vector_store_general_club:
            print(f"Using existing in-memory vector store for {mode}")
            return pdf_vector_store_general_club
        elif mode == "website_manager" and pdf_vector_website_manager:
            print(f"Using existing in-memory vector store for {mode}")
            return pdf_vector_website_manager
        elif mode == "website_student" and pdf_vector_website_student:
            print(f"Using existing in-memory vector store for {mode}")
            return pdf_vector_website_student
        
        # Set collection name
        collection_name = f"clubfaq_{mode}"
        
        # Create embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",  # Using the standard embedding model
            google_api_key=GEMINI_API_KEY
        )
        
        # Check if collection exists
        try:
            collections = chroma_client.list_collections()
            collection_exists = any(col.name == collection_name for col in collections)
            
            if collection_exists:
                try:
                    print(f"Loading existing ChromaDB collection '{collection_name}'")
                    vector_store = Chroma(
                        client=chroma_client, 
                        collection_name=collection_name,
                        embedding_function=embeddings
                    )
                    
                    # Store in appropriate global variable
                    if mode == "general_club":
                        pdf_vector_store_general_club = vector_store
                    elif mode == "website_manager":
                        pdf_vector_website_manager = vector_store
                    elif mode == "website_student":
                        pdf_vector_website_student = vector_store
                    
                    # Check if the collection has data
                    collection = chroma_client.get_collection(name=collection_name)
                    count = collection.count()
                    
                    if count > 0:
                        print(f"Found existing data in collection '{collection_name}' with {count} documents")
                        return vector_store
                    else:
                        print(f"Collection '{collection_name}' exists but is empty, creating new vectors")
                except Exception as e:
                    # Handle dimension mismatches
                    if "dimension" in str(e).lower():
                        print(f"Dimension mismatch detected, resetting collection '{collection_name}'")
                        chroma_client.delete_collection(name=collection_name)
                        collection_exists = False
                    else:
                        raise e
        
        except Exception as e:
            print(f"Error checking ChromaDB collection: {e}")
        
        # If no existing collection with data, create new vectors from PDF
        print(f"Creating new vector store for {mode} from {pdf_path}")
            
        # Check if PDF exists
        if not os.path.exists(pdf_path):
            print(f"Warning: PDF file {pdf_path} not found")
            # Create empty collection
            chroma_client.create_collection(name=collection_name)
            vector_store = Chroma(
                client=chroma_client,
                collection_name=collection_name,
                embedding_function=embeddings
            )
            return vector_store
            
        # Load and process the PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        # Split the documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # Smaller chunks for better retrieval
            chunk_overlap=50  # Less overlap to save space
        )
        chunks = text_splitter.split_documents(documents)
        
        print(f"Split PDF into {len(chunks)} chunks")
        
        # Create vector store with ChromaDB
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            client=chroma_client,
            collection_name=collection_name
        )
        
        # Store in the appropriate global variable
        if mode == "general_club":
            pdf_vector_store_general_club = vector_store
        elif mode == "website_manager":
            pdf_vector_website_manager = vector_store
        elif mode == "website_student":
            pdf_vector_website_student = vector_store
        
        print(f"Vector database for {mode} initialized successfully")
        return vector_store
        
    except Exception as e:
        print(f"Error initializing ChromaDB vector database: {e}")
        return None

def reset_collection(collection_name):
    """Delete an existing collection to reset it"""
    try:
        chroma_client.delete_collection(name=collection_name)
        print(f"Successfully deleted collection '{collection_name}'")
        return True
    except Exception as e:
        print(f"Error deleting collection: {e}")
        return False

def query_pdf(question, mode, context_prefix=""):
    """
    Query the ChromaDB vector database with a question using Gemini.
    
    Args:
        question: User's question
        mode: The mode to determine which PDF to use
        context_prefix: Additional context to prepend to the answer
        
    Returns:
        Answer from the vector database
    """
    try:
        if mode == "general_club":
            pdf_path = "resources/general_club.pdf"
        elif mode == "website_manager":
            pdf_path = "resources/website_manager.pdf"
        elif mode == "website_student":
            pdf_path = "resources/website_student.pdf"

        # Initialize vector store if not already done
        vector_store = initialize_vector_db(pdf_path, mode)
        if not vector_store:
            return "Sorry, I couldn't access the handbook database. Please try again later."
            
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        
        # Create a retriever
        retriever = vector_store.as_retriever(
            search_kwargs={"k": 6}  # Fetch 6 most relevant chunks
        )
        
        # Create a custom prompt template
        template = """
        You are a helpful assistant for a NDHU Club website.
        Use the following pieces of context to answer the question at the end.
        If you don't know the answer, just say you don't know. Don't try to make up an answer.
        Act as a chatbot, so if you dont know say you dont have the data to answer the question.
        Keep the answer concise and to the point.
        You may refer to the history of the conversation if needed. (If it exists)
        
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
            return f" {result['result']}"
        return result['result']
        
    except Exception as e:
        print(f"Error querying vector database: {e}")
        return "Sorry, I couldn't answer your question based on the handbook. Please try asking in a different way."

def cleanup_chromadb():
    """Clean up ChromaDB to free up space or reset"""
    try:
        # Only remove the directory if it exists
        if os.path.exists(CHROMA_DB_DIR):
            shutil.rmtree(CHROMA_DB_DIR)
            os.makedirs(CHROMA_DB_DIR, exist_ok=True)
            print(f"Successfully reset ChromaDB directory at {CHROMA_DB_DIR}")
            return True
    except Exception as e:
        print(f"Error cleaning up ChromaDB: {e}")
        return False