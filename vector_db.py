import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")  # Default to gcp-starter if not specified

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Global vector store references (for caching)
pdf_vector_store_general_club = None
pdf_vector_website_manager = None
pdf_vector_website_student = None


def initialize_vector_db(pdf_path, mode):
    """
    Initialize the vector database from a PDF file using Pinecone with Google's embeddings.
    
    Args:
        pdf_path: Path to the PDF file to index
        mode: Which mode/vector store to use
        
    Returns:
        Pinecone vector store object
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
        
        # Set index name and namespace
        index_name = "clubfaq"
        namespace = f"clubfaq_{mode}"
        
        # Create embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",  # Using the standard embedding model
            google_api_key=GEMINI_API_KEY
        )
        
        # Check if index exists, create if it doesn't
        try:
            # List all indexes
            indexes = pc.list_indexes()
            index_exists = any(idx.name == index_name for idx in indexes)
            
            if not index_exists:
                print(f"Creating new Pinecone index '{index_name}'")
                # Create a new index with serverless
                pc.create_index(
                    name=index_name,
                    dimension=768,  # Dimension for embedding-001
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-west-2"
                    )
                )
            
            # Get the index
            index = pc.Index(index_name)
            
            # Try to retrieve the vector store
            print(f"Connecting to Pinecone index '{index_name}' with namespace '{namespace}'")
            vector_store = PineconeVectorStore(
                index=index,
                embedding=embeddings,
                text_key="text",
                namespace=namespace
            )
            
            # Check if namespace has data by doing a simple query
            # If a namespace doesn't exist, Pinecone will create it the first time we add data
            stats = index.describe_index_stats()
            namespaces = stats.get("namespaces", {})
            
            # If namespace exists and has vectors, use it
            if namespace in namespaces and namespaces[namespace].get("vector_count", 0) > 0:
                print(f"Found existing data in namespace '{namespace}' with {namespaces[namespace]['vector_count']} vectors")
                
                # Store in appropriate global variable
                if mode == "general_club":
                    pdf_vector_store_general_club = vector_store
                elif mode == "website_manager":
                    pdf_vector_website_manager = vector_store
                elif mode == "website_student":
                    pdf_vector_website_student = vector_store
                
                return vector_store
            else:
                print(f"No existing data found in namespace '{namespace}', creating new vectors")
        
        except Exception as e:
            print(f"Error checking Pinecone index: {e}")
        
        # If no existing namespace with data, create new vectors from PDF
        print(f"Creating new vector store for {mode} from {pdf_path}")
            
        # Check if PDF exists
        if not os.path.exists(pdf_path):
            print(f"Warning: PDF file {pdf_path} not found")
            # Create empty vector store and return
            vector_store = PineconeVectorStore(
                index=pc.Index(index_name),
                embedding=embeddings,
                text_key="text",
                namespace=namespace
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
        
        # Create vector store with Pinecone
        vector_store = PineconeVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            index_name=index_name,
            namespace=namespace
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
        print(f"Error initializing Pinecone vector database: {e}")
        return None

def query_pdf(question, mode, context_prefix=""):
    """
    Query the Pinecone vector database with a question using Gemini.
    
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
            return f"{context_prefix} {result['result']}"
        return result['result']
        
    except Exception as e:
        print(f"Error querying vector database: {e}")
        return "Sorry, I couldn't answer your question based on the handbook. Please try asking in a different way."