"""
Test the specific query for KM150726VV wedding
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

wedding_code = "SJ310726VV"  # This one showed 7 unreplied messages

print("="*60)
print(f"QUERY: For {wedding_code}, are there any messages that aren't replied?")
print("="*60)

# Search for all messages for this wedding
all_km_messages = vector_store.similarity_search(
    "",
    k=100,
    filter={"event_code": wedding_code}
)

print(f"\nTotal messages for {wedding_code}: {len(all_km_messages)}")

# Filter for unreplied messages
unreplied_messages = []
for msg in all_km_messages:
    # Check needs_reply field
    if msg.metadata.get('needs_reply', False):
        unreplied_messages.append(msg)
    # Also check status-based logic
    elif msg.metadata.get('status', '').lower() in ['open', 'pending', 'waiting for client', 'in progress']:
        unreplied_messages.append(msg)

print(f"Unreplied messages: {len(unreplied_messages)}")

if unreplied_messages:
    print("\nUNREPLIED MESSAGES:")
    for i, msg in enumerate(unreplied_messages[:10]):  # Show up to 10
        print(f"\n{i+1}. {msg.metadata.get('title', 'No subject')}")
        print(f"   Status: {msg.metadata.get('status', 'Unknown')}")
        print(f"   Needs Reply: {msg.metadata.get('needs_reply', 'Not set')}")
        print(f"   Type: {msg.metadata.get('source_type', 'Unknown')}")
        
        # Check for contact information
        assignee = msg.metadata.get('assignee_name', msg.metadata.get('assignee_id', 'Unassigned'))
        assignee_email = msg.metadata.get('assignee_email', '')
        user_email = msg.metadata.get('user_email', '')
        
        print(f"   Assignee: {assignee}")
        if assignee_email:
            print(f"   Assignee Email: {assignee_email}")
        if user_email:
            print(f"   User Email: {user_email}")
        
        # Show content preview
        content_preview = msg.page_content[:100].replace('\n', ' ')
        print(f"   Preview: {content_preview}...")

    # Summary of contact availability
    with_assignee_email = sum(1 for msg in unreplied_messages if msg.metadata.get('assignee_email'))
    with_user_email = sum(1 for msg in unreplied_messages if msg.metadata.get('user_email'))
    
    print(f"\nCONTACT INFORMATION:")
    print(f"Messages with assignee email: {with_assignee_email}/{len(unreplied_messages)}")
    print(f"Messages with user email: {with_user_email}/{len(unreplied_messages)}")
else:
    print(f"\nGood news! No unreplied messages found for {wedding_code}.")

# Also check message types
print(f"\nMESSAGE TYPES FOR {wedding_code}:")
type_counts = {}
for msg in all_km_messages:
    msg_type = msg.metadata.get('source_type', 'unknown')
    type_counts[msg_type] = type_counts.get(msg_type, 0) + 1

for msg_type, count in type_counts.items():
    print(f"  {msg_type}: {count}")

# Check if we have the new enhanced documents
enhanced_count = sum(1 for msg in all_km_messages if 'needs_reply' in msg.metadata)
print(f"\nMessages with enhanced fields: {enhanced_count}/{len(all_km_messages)}")

print("\n" + "="*60)