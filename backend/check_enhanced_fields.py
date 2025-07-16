"""
Check if enhanced fields are being added to new documents
"""
import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from embeddings import get_embeddings_model

# Load environment variables from parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

# Initialize Pinecone
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index_name = os.environ.get("PINECONE_INDEX_NAME", "chat-langchain")
index = pc.Index(index_name)

# Initialize vector store
embeddings = get_embeddings_model()
vector_store = PineconeVectorStore(
    index=index,
    embedding=embeddings,
    text_key="text",
    namespace=""
)

print("Checking for enhanced inbox fields...")
print("="*60)

# Look for documents with the enhanced fields
enhanced_fields = [
    "needs_reply",
    "assignee_email",
    "user_email",
    "assignee_name",
    "user_type",
    "conversation_needs_reply"
]

# Search for recent documents
recent_docs = vector_store.similarity_search(
    "",
    k=50,
    filter={"source_type": {"$in": ["inbox_conversation_event", "inbox_conversation_user"]}}
)

print(f"Checking {len(recent_docs)} recent documents...")

# Check which enhanced fields are present
field_counts = {field: 0 for field in enhanced_fields}
docs_with_enhanced_fields = 0

for doc in recent_docs:
    has_enhanced_field = False
    for field in enhanced_fields:
        if field in doc.metadata:
            field_counts[field] += 1
            has_enhanced_field = True
    
    if has_enhanced_field:
        docs_with_enhanced_fields += 1

print(f"\nDocuments with enhanced fields: {docs_with_enhanced_fields}/{len(recent_docs)}")

print("\nEnhanced field presence:")
for field, count in field_counts.items():
    print(f"  {field}: {count} documents")

# Show a sample document with enhanced fields
print("\nSample documents:")
shown = 0
for doc in recent_docs:
    if any(field in doc.metadata for field in enhanced_fields):
        print(f"\nDocument {shown + 1}:")
        print(f"  Type: {doc.metadata.get('source_type')}")
        print(f"  Event Code: {doc.metadata.get('event_code', 'None')}")
        print(f"  Needs Reply: {doc.metadata.get('needs_reply', 'Not set')}")
        print(f"  User Email: {doc.metadata.get('user_email', 'Not set')}")
        print(f"  Assignee Email: {doc.metadata.get('assignee_email', 'Not set')}")
        print(f"  Title: {doc.metadata.get('title', 'No title')[:50]}")
        shown += 1
        if shown >= 3:
            break

if docs_with_enhanced_fields == 0:
    print("\nNo documents with enhanced fields found yet.")
    print("This could mean:")
    print("1. The enhanced ingestion is still processing")
    print("2. The new documents haven't been indexed yet")
    print("3. The ingestion may need to be restarted")

# Check the vector count trend
stats = index.describe_index_stats()
print(f"\nTotal vectors: {stats['total_vector_count']}")
print("If this number is still increasing, ingestion is ongoing...")