"""Simple check for private issues in vector database"""
import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

def check_for_private_issues():
    """Check if any private issues exist in vector DB"""
    
    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
    PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    
    print("Checking for private issues in vector database...")
    print("=" * 60)
    
    # Create a dummy vector for querying
    dummy_vector = [0.0] * 1024
    
    # Check different source types
    source_types_to_check = [
        "issue",
        "public_issue", 
        "task",
        "public_task",
        "private_issue",  # Just in case
        "comment"
    ]
    
    total_checked = 0
    private_found = 0
    
    for source_type in source_types_to_check:
        print(f"\nChecking source_type: {source_type}")
        
        try:
            # Query for this source type
            results = index.query(
                vector=dummy_vector,
                top_k=50,  # Check up to 50 of each type
                include_metadata=True,
                filter={"source_type": source_type}
            )
            
            if results['matches']:
                print(f"  Found {len(results['matches'])} documents of type '{source_type}'")
                
                # Check each document's metadata
                for match in results['matches']:
                    total_checked += 1
                    metadata = match.get('metadata', {})
                    
                    # Check various privacy indicators
                    is_private = False
                    privacy_reason = ""
                    
                    # Check is_private field
                    if metadata.get('is_private', False):
                        is_private = True
                        privacy_reason = "is_private=True"
                    
                    # Check if title contains private keywords
                    title = metadata.get('title', '').lower()
                    if any(word in title for word in ['private', 'confidential', 'internal', 'secret']):
                        is_private = True
                        privacy_reason = f"Title contains private keyword: {metadata.get('title', '')[:50]}"
                    
                    # Check source URL
                    source = metadata.get('source', '').lower()
                    if 'private' in source:
                        is_private = True
                        privacy_reason = "Source URL contains 'private'"
                    
                    if is_private:
                        private_found += 1
                        print(f"\n  [PRIVATE FOUND] Document: {match['id'][:20]}...")
                        print(f"    Reason: {privacy_reason}")
                        print(f"    Title: {metadata.get('title', 'N/A')[:80]}")
                        print(f"    Source Type: {metadata.get('source_type', 'N/A')}")
                        print(f"    is_private field: {metadata.get('is_private', 'Not set')}")
                
                # Summary for this type
                type_private = sum(1 for m in results['matches'] 
                                 if m.get('metadata', {}).get('is_private', False) or
                                 'private' in m.get('metadata', {}).get('title', '').lower())
                
                if type_private > 0:
                    print(f"  Summary: {type_private} private documents in this type")
            else:
                print(f"  No documents found for '{source_type}'")
                
        except Exception as e:
            print(f"  Error checking {source_type}: {str(e)[:100]}")
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY:")
    print(f"Total documents checked: {total_checked}")
    print(f"Private documents found: {private_found}")
    print(f"Percentage private: {(private_found/max(total_checked,1))*100:.1f}%")
    
    if private_found > 0:
        print("\n[WARNING] Private documents were found in the vector database!")
        print("These should be removed to ensure privacy compliance.")
    else:
        print("\n[OK] No private documents detected in the checked sample.")


if __name__ == "__main__":
    check_for_private_issues()