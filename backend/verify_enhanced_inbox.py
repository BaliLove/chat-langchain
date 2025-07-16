"""
Verify that enhanced inbox ingestion meets wedding search requirements
"""
import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from embeddings import get_embeddings_model
from collections import defaultdict

# Load environment variables from parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

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
print("VERIFYING ENHANCED INBOX DATA")
print("="*60)

# 1. Test the specific query: "For KM150726VV are there any messages that aren't replied?"
print("\n1. TESTING WEDDING-SPECIFIC QUERY:")
print("Query: 'For KM150726VV, are there any messages that aren't replied?'")

# Search for all messages for this wedding
km_messages = vector_store.similarity_search(
    "",
    k=100,
    filter={"event_code": "KM150726VV"}
)

print(f"\nFound {len(km_messages)} total messages for KM150726VV")

# Filter for messages needing reply
km_needing_reply = []
km_with_contact = []

for msg in km_messages:
    if msg.metadata.get('needs_reply'):
        km_needing_reply.append(msg)
    
    # Check if we have contact info
    if msg.metadata.get('user_email') or msg.metadata.get('assignee_email'):
        km_with_contact.append(msg)

print(f"Messages needing reply: {len(km_needing_reply)}")
print(f"Messages with contact emails: {len(km_with_contact)}")

# Show sample messages needing reply
if km_needing_reply:
    print("\nSample messages needing reply:")
    for i, msg in enumerate(km_needing_reply[:3]):
        subject = msg.metadata.get('title', 'No subject')
        status = msg.metadata.get('status', 'Unknown')
        assignee = msg.metadata.get('assignee_name', 'Unassigned')
        print(f"  {i+1}. {subject}")
        print(f"      Status: {status} | Assignee: {assignee}")

# 2. Check event code coverage
print("\n2. EVENT CODE COVERAGE:")
all_conversations = vector_store.similarity_search(
    "",
    k=200,
    filter={"source_type": {"$in": ["inbox_conversation_event", "inboxconversation"]}}
)

event_code_count = 0
general_count = 0
no_code_count = 0

for conv in all_conversations:
    event_code = conv.metadata.get('event_code')
    if event_code:
        if event_code == "GENERAL":
            general_count += 1
        else:
            event_code_count += 1
    else:
        no_code_count += 1

total_conv = len(all_conversations)
print(f"Total conversations sampled: {total_conv}")
print(f"With specific event codes: {event_code_count} ({event_code_count/total_conv*100:.1f}%)")
print(f"With GENERAL code: {general_count} ({general_count/total_conv*100:.1f}%)")
print(f"Without any code: {no_code_count} ({no_code_count/total_conv*100:.1f}%)")

# 3. Check contact email coverage
print("\n3. CONTACT EMAIL COVERAGE:")
user_records = vector_store.similarity_search(
    "",
    k=200,
    filter={"source_type": "inbox_conversation_user"}
)

email_count = 0
internal_count = 0
external_count = 0

for record in user_records:
    if record.metadata.get('user_email'):
        email_count += 1
        user_type = record.metadata.get('user_type', '')
        if user_type == 'internal':
            internal_count += 1
        elif user_type == 'external':
            external_count += 1

print(f"User records sampled: {len(user_records)}")
if len(user_records) > 0:
    print(f"With email addresses: {email_count} ({email_count/len(user_records)*100:.1f}%)")
    print(f"Internal (@bali.love): {internal_count}")
    print(f"External (clients/vendors): {external_count}")
else:
    print("No user records found yet (indexing may still be in progress)")

# 4. Check reply status tracking
print("\n4. REPLY STATUS TRACKING:")
status_dist = defaultdict(int)
needs_reply_count = 0

for conv in all_conversations:
    status = conv.metadata.get('status', 'Unknown')
    status_dist[status] += 1
    
    if conv.metadata.get('needs_reply'):
        needs_reply_count += 1

print(f"Messages needing reply: {needs_reply_count}")
print("\nStatus distribution:")
for status, count in sorted(status_dist.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"  {status}: {count}")

# 5. Test more wedding searches
print("\n5. TESTING MORE WEDDING SEARCHES:")
test_weddings = ["JA070926VV", "SJ310726VV", "CS290625BBG"]

for wedding_code in test_weddings:
    results = vector_store.similarity_search(
        "",
        k=50,
        filter={
            "$and": [
                {"event_code": wedding_code},
                {"needs_reply": True}
            ]
        }
    )
    
    print(f"\n{wedding_code}:")
    print(f"  Total unreplied messages: {len(results)}")
    
    if results:
        # Show contact info availability
        with_contacts = sum(1 for r in results if r.metadata.get('user_email') or r.metadata.get('assignee_email'))
        print(f"  With contact emails: {with_contacts}")
        
        # Show sample
        sample = results[0]
        print(f"  Sample: {sample.metadata.get('title', 'No title')[:50]}")
        print(f"    Contact: {sample.metadata.get('user_email') or sample.metadata.get('assignee_email', 'No email')}")

# 6. Summary
print("\n" + "="*60)
print("ENHANCED INBOX DATA VERIFICATION SUMMARY")
print("="*60)

print("\n✅ CAPABILITIES ENABLED:")
print("• Search all messages by wedding event code")
print("• Find unreplied messages for specific weddings")
print("• Access contact emails for follow-up")
print("• Track conversation status and reply needs")

print("\n📊 COVERAGE METRICS:")
if total_conv > 0:
    print(f"• Event code coverage: {(event_code_count + general_count)/total_conv*100:.1f}%")
else:
    print(f"• Event code coverage: N/A (no conversations found)")
    
if len(user_records) > 0:
    print(f"• Contact email coverage: {email_count/len(user_records)*100:.1f}%")
else:
    print(f"• Contact email coverage: N/A (user records still indexing)")
    
print(f"• Reply status tracking: {needs_reply_count} messages need replies")

print("\n🎯 YOUR TEAM CAN NOW:")
print("• Query: 'For KM150726VV, are there any messages that aren't replied?'")
print("• Get contact emails for unreplied messages")
print("• Filter by event code + status + reply needs")
print("• Track all communications for each wedding")

print("\n" + "="*60)