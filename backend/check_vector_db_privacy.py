"""Check vector database for any private issues that might have been indexed"""
import os
from dotenv import load_dotenv
from pinecone import Pinecone
import json

load_dotenv()

def check_vector_db_for_private_content():
    """Query vector database to check for private content"""
    
    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
    PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    
    # Get index statistics
    stats = index.describe_index_stats()
    print("Vector Database Statistics:")
    print(f"Total vectors: {stats['total_vector_count']}")
    print("\n" + "=" * 60)
    
    # Query for issue-related documents
    print("\nSearching for issue-related documents in vector DB...")
    
    # Sample query to get some vectors with metadata
    # Using a dummy vector since we just want to see metadata
    dummy_vector = [0.0] * 1024  # Assuming 1024 dimensions
    
    try:
        # Query for documents with various source types
        source_types = ["issue", "public_issue", "task", "public_task", "comment", "training"]
        
        for source_type in source_types:
            print(f"\nChecking source_type: {source_type}")
            
            # Query with metadata filter
            results = index.query(
                vector=dummy_vector,
                top_k=10,
                include_metadata=True,
                filter={"source_type": source_type}
            )
            
            if results['matches']:
                print(f"  Found {len(results['matches'])} documents")
                
                # Check for privacy indicators
                for i, match in enumerate(results['matches'][:3]):  # Show first 3
                    metadata = match.get('metadata', {})
                    print(f"\n  Document {i+1}:")
                    print(f"    ID: {match['id']}")
                    print(f"    Source: {metadata.get('source', 'N/A')}")
                    print(f"    Title: {metadata.get('title', 'N/A')}")
                    
                    # Check privacy-related fields
                    if 'is_private' in metadata:
                        print(f"    is_private: {metadata['is_private']} ⚠️")
                    if 'is_public' in metadata:
                        print(f"    is_public: {metadata['is_public']}")
                    if 'readStatus' in metadata:
                        print(f"    readStatus: {metadata['readStatus']}")
                    
                    # Check if content seems private
                    if 'private' in str(metadata).lower() or 'confidential' in str(metadata).lower():
                        print("    ⚠️ POTENTIAL PRIVACY CONCERN IN METADATA")
            else:
                print(f"  No documents found")
        
        # Also do a broader search for any privacy indicators
        print("\n\nBroad search for privacy indicators...")
        
        # Search without filters to sample random documents
        general_results = index.query(
            vector=dummy_vector,
            top_k=100,
            include_metadata=True
        )
        
        privacy_concerns = []
        source_type_counts = {}
        
        for match in general_results['matches']:
            metadata = match.get('metadata', {})
            source_type = metadata.get('source_type', 'unknown')
            
            # Count source types
            source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
            
            # Check for privacy indicators
            metadata_str = str(metadata).lower()
            if any(term in metadata_str for term in ['private', 'confidential', 'is_private', 'internal', 'secret']):
                privacy_concerns.append({
                    'id': match['id'],
                    'source': metadata.get('source', 'N/A'),
                    'title': metadata.get('title', 'N/A'),
                    'source_type': source_type,
                    'metadata': metadata
                })
        
        print(f"\nDocument distribution in sample of 100:")
        for st, count in sorted(source_type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {st}: {count}")
        
        if privacy_concerns:
            print(f"\n⚠️ FOUND {len(privacy_concerns)} DOCUMENTS WITH PRIVACY INDICATORS:")
            for concern in privacy_concerns[:5]:  # Show first 5
                print(f"\n  Document: {concern['id']}")
                print(f"  Source Type: {concern['source_type']}")
                print(f"  Title: {concern['title']}")
                print(f"  Metadata: {json.dumps(concern['metadata'], indent=4)}")
        else:
            print("\n✅ No documents with privacy indicators found in sample")
            
    except Exception as e:
        print(f"Error querying vector database: {e}")


if __name__ == "__main__":
    check_vector_db_for_private_content()