"""
Analyze existing inbox data in the vector database to understand current state
"""
import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from embeddings import get_embeddings_model
from collections import defaultdict

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

print("\\n" + "="*60)
print("ANALYZING EXISTING INBOX DATA")
print("="*60)

# 1. Check inbox conversation types
print("\\n1. INBOX CONVERSATION TYPES:")
inbox_types = ["inboxconversation", "inbox_conversation_event", "inboxconversationuser"]

for inbox_type in inbox_types:
    results = vector_store.similarity_search(
        "",
        k=100,
        filter={"source_type": inbox_type}
    )
    print(f"  {inbox_type}: {len(results)} documents")
    
    # Show sample event codes for conversations
    if inbox_type in ["inboxconversation", "inbox_conversation_event"] and results:
        event_codes = set()
        for doc in results[:20]:
            event_code = doc.metadata.get('event_code')
            if event_code:
                event_codes.add(event_code)
        
        if event_codes:
            print(f"    Sample event codes: {', '.join(sorted(list(event_codes))[:10])}")

# 2. Check event code coverage
print("\\n2. EVENT CODE COVERAGE:")
all_inbox_conversations = vector_store.similarity_search(
    "",
    k=200,
    filter={"source_type": {"$in": ["inboxconversation", "inbox_conversation_event"]}}
)

event_code_stats = defaultdict(int)
no_event_code_count = 0

for doc in all_inbox_conversations:
    event_code = doc.metadata.get('event_code')
    if event_code:
        event_code_stats[event_code] += 1
    else:
        no_event_code_count += 1

print(f"Total conversations analyzed: {len(all_inbox_conversations)}")
print(f"With event codes: {len(all_inbox_conversations) - no_event_code_count}")
print(f"Without event codes: {no_event_code_count}")

if event_code_stats:
    print("\\nTop event codes in conversations:")
    for code, count in sorted(event_code_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {code}: {count} conversations")

# 3. Check contact email information
print("\\n3. CONTACT EMAIL INFORMATION:")
user_records = vector_store.similarity_search(
    "",
    k=100,
    filter={"source_type": "inboxconversationuser"}
)

contact_stats = {
    "total_user_records": len(user_records),
    "with_emails": 0,
    "internal_contacts": 0,
    "external_contacts": 0
}

sample_emails = []
for doc in user_records:
    user_email = doc.metadata.get('user_email')
    if user_email:
        contact_stats["with_emails"] += 1
        if "@bali.love" in user_email:
            contact_stats["internal_contacts"] += 1
        else:
            contact_stats["external_contacts"] += 1
        
        if len(sample_emails) < 5:
            sample_emails.append(user_email)

print(f"Total user records: {contact_stats['total_user_records']}")
print(f"With email addresses: {contact_stats['with_emails']}")
print(f"Internal contacts: {contact_stats['internal_contacts']}")
print(f"External contacts: {contact_stats['external_contacts']}")

if sample_emails:
    print(f"Sample emails: {', '.join(sample_emails)}")

# 4. Check reply status information
print("\\n4. REPLY STATUS INFORMATION:")
conversations_with_status = vector_store.similarity_search(
    "",
    k=100,
    filter={"source_type": {"$in": ["inboxconversation", "inbox_conversation_event"]}}
)

status_stats = defaultdict(int)
needs_reply_count = 0

for doc in conversations_with_status:
    status = doc.metadata.get('status')
    needs_reply = doc.metadata.get('needs_reply')
    
    if status:
        status_stats[status] += 1
    
    if needs_reply:
        needs_reply_count += 1

print(f"Status distribution:")
for status, count in sorted(status_stats.items(), key=lambda x: x[1], reverse=True):
    print(f"  {status}: {count}")

print(f"\\nMessages needing reply: {needs_reply_count}")

# 5. Test wedding-specific search capability
print("\\n5. WEDDING-SPECIFIC SEARCH CAPABILITY:")
sample_event_codes = ["KM150726VV", "JA070926VV", "SJ310726VV"]

for event_code in sample_event_codes:
    # Search for all data related to this event
    results = vector_store.similarity_search(
        "",
        k=50,
        filter={"event_code": event_code}
    )
    
    if results:
        print(f"\\nEvent {event_code}: {len(results)} total records")
        
        # Break down by type
        type_counts = defaultdict(int)
        needs_reply_count = 0
        
        for doc in results:
            doc_type = doc.metadata.get('source_type', 'unknown')
            type_counts[doc_type] += 1
            
            if doc.metadata.get('needs_reply'):
                needs_reply_count += 1
        
        print(f"  Types: {dict(type_counts)}")
        print(f"  Needs reply: {needs_reply_count}")
        
        # Show sample conversation
        for doc in results[:1]:
            if doc.metadata.get('source_type') in ['inboxconversation', 'inbox_conversation_event']:
                title = doc.metadata.get('title', 'No title')
                status = doc.metadata.get('status', 'Unknown')
                print(f"  Sample: {title} (Status: {status})")
    else:
        print(f"\\nEvent {event_code}: No records found")

# 6. Summary and recommendations
print("\\n" + "="*60)
print("SUMMARY AND RECOMMENDATIONS")
print("="*60)

total_conversations = len(all_inbox_conversations)
with_event_codes = len(all_inbox_conversations) - no_event_code_count
event_coverage = (with_event_codes / total_conversations * 100) if total_conversations > 0 else 0

email_coverage = (contact_stats['with_emails'] / contact_stats['total_user_records'] * 100) if contact_stats['total_user_records'] > 0 else 0

print(f"\\nCurrent Status:")
print(f"- Event code coverage: {event_coverage:.1f}%")
print(f"- Contact email coverage: {email_coverage:.1f}%")
print(f"- Total event codes: {len(event_code_stats)}")
print(f"- Messages needing reply: {needs_reply_count}")

print(f"\\nEnabled Use Cases:")
print(f"✓ Search all messages for specific wedding by event code")
print(f"✓ Find unreplied messages for specific events")
print(f"✓ Get contact information for wedding participants")
print(f"✓ Track conversation status across events")

print(f"\\nTo Answer: 'For KM150726VV, are there any messages that aren't replied?'")
print(f"Filter: event_code='KM150726VV' AND needs_reply=True")

print(f"\\nNext Steps:")
if event_coverage < 100:
    print(f"- Improve event code mapping (currently {event_coverage:.1f}% coverage)")
if email_coverage < 100:
    print(f"- Enhance contact email capture (currently {email_coverage:.1f}% coverage)")
if no_event_code_count > 0:
    print(f"- Assign event codes to {no_event_code_count} messages without codes")

print("="*60)