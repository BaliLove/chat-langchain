"""
Check inbox messages in the vector database
"""
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

# Get stats
stats = index.describe_index_stats()
print(f"Vector Database Statistics:")
print(f"Total vectors: {stats['total_vector_count']}")

# Initialize vector store for queries
embeddings = get_embeddings_model()
vector_store = PineconeVectorStore(
    index=index,
    embedding=embeddings,
    text_key="text",
    namespace=""
)

print("\n" + "="*60)
print("\nSearching for inbox messages in vector DB...")

# Search for InboxConversation
print("\nChecking source_type: inboxconversation")
results = vector_store.similarity_search(
    "",
    k=10,
    filter={"source_type": "inboxconversation"}
)
print(f"  Found {len(results)} documents")

if results:
    for i, doc in enumerate(results[:3]):
        print(f"\n  Document {i+1}:")
        print(f"    ID: {doc.metadata.get('_id', 'N/A')}")
        print(f"    Source: {doc.metadata.get('source', 'N/A')}")
        print(f"    Title: {doc.metadata.get('title', 'N/A')}")
        print(f"    Status: {doc.metadata.get('status', 'N/A')}")
        if doc.metadata.get('event_id'):
            print(f"    Event ID: {doc.metadata.get('event_id')}")

# Search for InboxConversationUser
print("\n\nChecking source_type: inboxconversationuser")
results = vector_store.similarity_search(
    "",
    k=10,
    filter={"source_type": "inboxconversationuser"}
)
print(f"  Found {len(results)} documents")

if results:
    for i, doc in enumerate(results[:3]):
        print(f"\n  Document {i+1}:")
        print(f"    ID: {doc.metadata.get('_id', 'N/A')}")
        print(f"    Source: {doc.metadata.get('source', 'N/A')}")
        print(f"    Title: {doc.metadata.get('title', 'N/A')}")
        if doc.metadata.get('no_reply_needed'):
            print(f"    No reply needed: True")

# Count messages by status
print("\n\n" + "="*60)
print("Message Status Distribution (sample):")
statuses = ["Solved", "Open", "In Progress", "Pending"]
for status in statuses:
    results = vector_store.similarity_search(
        "",
        k=100,
        filter={"source_type": "inboxconversation", "status": status}
    )
    if results:
        print(f"  {status}: {len(results)} messages")

# Search for event-linked messages
print("\n\nSearching for messages linked to events...")
results = vector_store.similarity_search(
    "event",
    k=20,
    filter={"source_type": "inboxconversation"}
)
event_linked = [doc for doc in results if doc.metadata.get('event_id')]
print(f"Found {len(event_linked)} messages linked to events (in sample)")

print("\n" + "="*60)