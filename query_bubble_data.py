"""Query the ingested Bubble data from Pinecone"""

import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
import logging

# Load environment
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def query_bubble_data():
    """Query Bubble data with various filters"""
    
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
    
    print("=== Bubble Data Query Tool ===\n")
    
    # 1. Check what data types we have
    print("1. Checking available data types...")
    
    data_types = ["event", "venue", "product", "vendor", "training_module", "employee_training_plan"]
    
    for dtype in data_types:
        try:
            results = vector_store.similarity_search(
                "",  # Empty query
                k=1,
                filter={"source_type": dtype}
            )
            if results:
                print(f"   [OK] {dtype}: Data available")
            else:
                print(f"   [-] {dtype}: No data")
        except Exception as e:
            print(f"   [ERROR] {dtype}: {e}")
    
    # 2. Sample queries
    print("\n2. Sample Queries...")
    
    queries = [
        {
            "query": "wedding venues in Uluwatu",
            "filter": {"source_type": {"$in": ["venue", "event"]}}
        },
        {
            "query": "wedding event planning",
            "filter": {"source_type": "event", "is_wedding": True}
        },
        {
            "query": "large capacity venues",
            "filter": {"source_type": "venue"}
        },
        {
            "query": "preferred vendors for events",
            "filter": {"source_type": "vendor", "is_preferred": True}
        },
        {
            "query": "event services and products",
            "filter": {"source_type": "product"}
        }
    ]
    
    for q in queries:
        print(f"\n   Query: '{q['query']}'")
        if q.get('filter'):
            print(f"   Filter: {q['filter']}")
        
        try:
            results = vector_store.similarity_search(
                q["query"],
                k=3,
                filter=q.get("filter")
            )
            
            if results:
                print(f"   Found {len(results)} results:")
                for i, doc in enumerate(results, 1):
                    print(f"\n   Result {i}:")
                    print(f"     Type: {doc.metadata.get('source_type')}")
                    print(f"     Name: {doc.metadata.get('name', 'N/A')}")
                    
                    # Show relevant metadata
                    if doc.metadata.get('source_type') == 'venue':
                        print(f"     Area: {doc.metadata.get('area', 'N/A')}")
                        print(f"     Capacity: {doc.metadata.get('capacity', 'N/A')}")
                    elif doc.metadata.get('source_type') == 'event':
                        print(f"     Status: {doc.metadata.get('status', 'N/A')}")
                        print(f"     Type: {doc.metadata.get('event_type', 'N/A')}")
                        print(f"     Code: {doc.metadata.get('code', 'N/A')}")
                    elif doc.metadata.get('source_type') == 'vendor':
                        print(f"     Preferred: {doc.metadata.get('is_preferred', False)}")
                    
                    # Content preview
                    preview = doc.page_content[:120] + "..." if len(doc.page_content) > 120 else doc.page_content
                    print(f"     Content: {preview}")
            else:
                print("   No results found.")
                
        except Exception as e:
            print(f"   Error: {e}")
    
    # 3. Show recent events
    print("\n\n3. Recent Events...")
    
    try:
        # Get events with status
        results = vector_store.similarity_search(
            "recent events",
            k=5,
            filter={
                "source_type": "event",
                "status": {"$in": ["Lead", "Confirmed", "Active"]}
            }
        )
        
        if results:
            print(f"   Found {len(results)} recent events:")
            for doc in results:
                name = doc.metadata.get('name', 'Unnamed')
                status = doc.metadata.get('status', 'Unknown')
                code = doc.metadata.get('code', 'N/A')
                print(f"   - {name} (Status: {status}, Code: {code})")
        else:
            print("   No recent events found")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. Interactive query mode
    print("\n\n4. Interactive Query Mode")
    print("   Enter your queries below (type 'exit' to quit):\n")
    
    while True:
        query = input("   Your query: ").strip()
        
        if query.lower() == 'exit':
            break
        
        if not query:
            continue
        
        try:
            # Search across all relevant types
            results = vector_store.similarity_search(
                query,
                k=5,
                filter={"source_type": {"$in": ["event", "venue", "product", "vendor"]}}
            )
            
            if results:
                print(f"\n   Found {len(results)} results:")
                for i, doc in enumerate(results, 1):
                    print(f"\n   Result {i}:")
                    print(f"     Type: {doc.metadata.get('source_type')}")
                    print(f"     Name: {doc.metadata.get('name', 'N/A')}")
                    preview = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                    print(f"     Content: {preview}")
            else:
                print("   No results found.")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        print()  # Blank line for readability


if __name__ == "__main__":
    query_bubble_data()