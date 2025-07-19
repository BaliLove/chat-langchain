"""Check what source_types exist for issues in the vector database"""
import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from embeddings import get_embeddings_model

load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index_name = os.environ.get("PINECONE_INDEX_NAME", "chat-langchain")
index = pc.Index(index_name)

# Initialize vector store for queries
embeddings = get_embeddings_model()
vector_store = PineconeVectorStore(
    index=index,
    embedding=embeddings,
    text_key="text",
    namespace=""
)

print("Checking source_types for issue-related documents...")
print("=" * 60)

# Check different possible source_types
source_types_to_check = ["issue", "public_issue", "task", "public_task", "comment"]

for source_type in source_types_to_check:
    print(f"\nChecking source_type: '{source_type}'")
    try:
        results = vector_store.similarity_search(
            "",
            k=5,
            filter={"source_type": source_type}
        )
        print(f"  Found {len(results)} documents")
        
        if results:
            # Show a sample
            doc = results[0]
            print(f"  Sample metadata:")
            print(f"    - title: {doc.metadata.get('title', 'N/A')}")
            print(f"    - category: {doc.metadata.get('category', 'N/A')}")
            print(f"    - status: {doc.metadata.get('status', 'N/A')}")
            print(f"    - source: {doc.metadata.get('source', 'N/A')[:50]}...")
    except Exception as e:
        print(f"  Error: {e}")

# Also check for inbox_conversation_user which seems to be returned
print(f"\nChecking source_type: 'inbox_conversation_user'")
try:
    results = vector_store.similarity_search(
        "",
        k=5,
        filter={"source_type": "inbox_conversation_user"}
    )
    print(f"  Found {len(results)} documents")
    
    if results:
        # Show a sample
        doc = results[0]
        print(f"  Sample metadata:")
        print(f"    - title: {doc.metadata.get('title', 'N/A')}")
        print(f"    - category: {doc.metadata.get('category', 'N/A')}")
        print(f"    - user_email: {doc.metadata.get('user_email', 'N/A')}")
        print(f"    - source: {doc.metadata.get('source', 'N/A')[:50]}...")
except Exception as e:
    print(f"  Error: {e}")