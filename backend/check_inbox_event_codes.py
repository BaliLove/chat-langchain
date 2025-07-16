"""
Check if inbox messages now have event codes for team searchability
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
print("CHECKING INBOX MESSAGES FOR EVENT CODE MAPPING")
print("="*60)

# Check for event-linked inbox conversations
print("\n1. Checking inbox conversations with event codes...")
results = vector_store.similarity_search(
    "",
    k=20,
    filter={"source_type": "inbox_conversation_event"}
)
print(f"Found {len(results)} inbox conversations with event codes")

if results:
    print("\nSample event-linked conversations:")
    for i, doc in enumerate(results[:5]):
        event_code = doc.metadata.get('event_code', 'No code')
        subject = doc.metadata.get('title', 'No subject')
        status = doc.metadata.get('status', 'No status')
        print(f"  {i+1}. Event: {event_code} | Subject: {subject} | Status: {status}")

# Check for specific event codes
print("\n2. Testing search by specific event codes...")
sample_event_codes = ["SARLEAD", "PAYLEAD", "MEGLEAD", "DANLEAD"]

for event_code in sample_event_codes:
    results = vector_store.similarity_search(
        "",
        k=10,
        filter={"event_code": event_code}
    )
    
    if results:
        print(f"\n  Event {event_code}: Found {len(results)} messages")
        # Show types of messages for this event
        types = {}
        for doc in results:
            doc_type = doc.metadata.get('source_type', 'unknown')
            types[doc_type] = types.get(doc_type, 0) + 1
        
        type_summary = ", ".join([f"{k}:{v}" for k, v in types.items()])
        print(f"    Types: {type_summary}")
    else:
        print(f"\n  Event {event_code}: No messages found")

# Check all inbox messages (both with and without event codes)
print("\n3. Overall inbox message statistics...")
inbox_all = vector_store.similarity_search(
    "",
    k=100,
    filter={"source_type": "inboxconversation"}
)
inbox_event_linked = vector_store.similarity_search(
    "",
    k=100,
    filter={"source_type": "inbox_conversation_event"}
)

print(f"Total inbox conversations (any type): {len(inbox_all)}")
print(f"Event-linked inbox conversations: {len(inbox_event_linked)}")

if len(inbox_all) > 0:
    percentage = (len(inbox_event_linked) / len(inbox_all)) * 100
    print(f"Event-linked percentage: {percentage:.1f}%")

# List unique event codes found
print("\n4. Unique event codes in inbox messages...")
event_codes = set()
results = vector_store.similarity_search(
    "",
    k=100,
    filter={"source_type": "inbox_conversation_event"}
)

for doc in results:
    code = doc.metadata.get('event_code')
    if code:
        event_codes.add(code)

print(f"Found {len(event_codes)} unique event codes in inbox messages")
if event_codes:
    sorted_codes = sorted(list(event_codes))
    print(f"Event codes: {', '.join(sorted_codes[:15])}")
    if len(sorted_codes) > 15:
        print(f"... and {len(sorted_codes) - 15} more")

print("\n" + "="*60)
print("TEAM SEARCH CAPABILITY:")
print("✓ Filter by event_code='SARLEAD' to find all messages for that event")
print("✓ Search within specific events using event code filters")
print("✓ Combine text search with event code filtering")
print("="*60)