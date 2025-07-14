"""Query training data specifically from Pinecone"""

import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
import logging

# Load environment
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def query_training_data():
    """Query training data with metadata filtering"""
    
    # Initialize embeddings and vector store
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        dimensions=1024,
        chunk_size=200
    )
    
    vector_store = PineconeVectorStore(
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        embedding=embeddings
    )
    
    # Sample queries with metadata filtering
    queries = [
        {
            "query": "customer service training",
            "filter": {"source_type": "training_module"}
        },
        {
            "query": "John Smith training progress",
            "filter": {"source_type": "employee_training_plan"}
        },
        {
            "query": "January training sessions",
            "filter": {"source_type": "training_session"}
        },
        {
            "query": "health and safety",
            "filter": {"source_type": {"$in": ["training_module", "training_session"]}}
        }
    ]
    
    print("=== Training Data Queries ===\n")
    
    for q in queries:
        print(f"Query: {q['query']}")
        print(f"Filter: {q.get('filter', 'None')}")
        
        try:
            # Search with metadata filter
            results = vector_store.similarity_search(
                q["query"],
                k=5,
                filter=q.get("filter")
            )
            
            if results:
                print(f"Found {len(results)} results:")
                for i, doc in enumerate(results, 1):
                    print(f"\n  Result {i}:")
                    print(f"    Type: {doc.metadata.get('source_type', 'unknown')}")
                    print(f"    Title: {doc.metadata.get('title', doc.metadata.get('employee_name', 'N/A'))}")
                    
                    # Show relevant metadata
                    if doc.metadata.get('source_type') == 'training_module':
                        print(f"    Category: {doc.metadata.get('category', 'N/A')}")
                        print(f"    Duration: {doc.metadata.get('duration', 'N/A')}")
                    elif doc.metadata.get('source_type') == 'training_session':
                        print(f"    Date: {doc.metadata.get('date', 'N/A')}")
                        print(f"    Instructor: {doc.metadata.get('instructor', 'N/A')}")
                    elif doc.metadata.get('source_type') == 'employee_training_plan':
                        print(f"    Department: {doc.metadata.get('department', 'N/A')}")
                        print(f"    Status: {doc.metadata.get('status', 'N/A')}")
                    
                    # Content preview
                    preview = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                    print(f"    Content: {preview}")
            else:
                print("  No results found.")
                
        except Exception as e:
            print(f"  Error: {e}")
        
        print("\n" + "-" * 60 + "\n")
    
    # Show all training data types
    print("=== All Training Data in Index ===\n")
    
    training_types = ["training_module", "training_session", "employee_training_plan"]
    
    for t in training_types:
        try:
            # Get all documents of this type
            results = vector_store.similarity_search(
                "",  # Empty query to get all
                k=10,
                filter={"source_type": t}
            )
            
            print(f"{t}: {len(results)} documents")
            
            if results:
                for doc in results[:3]:  # Show first 3
                    title = doc.metadata.get('title', doc.metadata.get('employee_name', 'N/A'))
                    print(f"  - {title}")
                    
        except Exception as e:
            print(f"{t}: Error - {e}")
        
        print()


if __name__ == "__main__":
    query_training_data()