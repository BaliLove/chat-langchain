"""Check the history of issue ingestions in the vector database"""
import os
from dotenv import load_dotenv
from pinecone import Pinecone
from collections import defaultdict
from datetime import datetime

load_dotenv()

def analyze_issue_ingestions():
    """Analyze what issue data exists in the vector DB"""
    
    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
    PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    
    print("Analyzing issue data in vector database...")
    print("=" * 60)
    
    # Create a dummy vector for querying
    dummy_vector = [0.0] * 1024
    
    # Get a larger sample to analyze
    results = index.query(
        vector=dummy_vector,
        top_k=1000,  # Get a large sample
        include_metadata=True
    )
    
    # Analyze the results
    source_type_counts = defaultdict(int)
    issue_related_docs = []
    privacy_field_stats = {
        "has_is_private": 0,
        "is_private_true": 0,
        "is_private_false": 0,
        "no_privacy_field": 0
    }
    
    for match in results['matches']:
        metadata = match.get('metadata', {})
        source_type = metadata.get('source_type', 'unknown')
        source_type_counts[source_type] += 1
        
        # Collect issue-related documents
        if any(term in source_type.lower() for term in ['issue', 'task', 'comment']):
            issue_related_docs.append({
                'id': match['id'],
                'source_type': source_type,
                'title': metadata.get('title', 'N/A'),
                'is_private': metadata.get('is_private'),
                'is_public': metadata.get('is_public'),
                'source': metadata.get('source', '')
            })
            
            # Check privacy field presence
            if 'is_private' in metadata:
                privacy_field_stats["has_is_private"] += 1
                if metadata['is_private']:
                    privacy_field_stats["is_private_true"] += 1
                else:
                    privacy_field_stats["is_private_false"] += 1
            else:
                privacy_field_stats["no_privacy_field"] += 1
    
    # Print analysis
    print("\nSOURCE TYPE DISTRIBUTION (sample of 1000):")
    for source_type, count in sorted(source_type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source_type}: {count}")
    
    print(f"\nISSUE-RELATED DOCUMENTS: {len(issue_related_docs)}")
    
    # Group by source type
    by_type = defaultdict(list)
    for doc in issue_related_docs:
        by_type[doc['source_type']].append(doc)
    
    print("\nISSUE DATA BY TYPE:")
    for source_type, docs in by_type.items():
        print(f"\n  {source_type}: {len(docs)} documents")
        
        # Check privacy fields in this type
        with_privacy = sum(1 for d in docs if d['is_private'] is not None)
        private_true = sum(1 for d in docs if d['is_private'] is True)
        public_marked = sum(1 for d in docs if d.get('is_public') is True)
        
        print(f"    - With is_private field: {with_privacy}")
        print(f"    - Marked as private (is_private=True): {private_true}")
        print(f"    - Marked as public (is_public=True): {public_marked}")
        
        # Show a few examples
        print(f"    - Examples:")
        for doc in docs[:3]:
            title_preview = doc['title'][:60] + "..." if len(doc['title']) > 60 else doc['title']
            print(f"      * {title_preview}")
            print(f"        is_private: {doc['is_private']}, is_public: {doc.get('is_public', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("PRIVACY FIELD ANALYSIS:")
    print(f"Documents with is_private field: {privacy_field_stats['has_is_private']}")
    print(f"  - is_private=True: {privacy_field_stats['is_private_true']}")
    print(f"  - is_private=False: {privacy_field_stats['is_private_false']}")
    print(f"Documents without privacy field: {privacy_field_stats['no_privacy_field']}")
    
    # Check if we need to clean up
    if privacy_field_stats['is_private_true'] > 0:
        print("\n[WARNING] Found documents marked as private!")
        print("These should be removed from the vector database.")
    
    # Check for old vs new ingestion patterns
    old_pattern = sum(1 for d in issue_related_docs if d['source_type'] in ['issue', 'task', 'comment'])
    new_pattern = sum(1 for d in issue_related_docs if d['source_type'] in ['public_issue', 'public_task'])
    
    print(f"\nINGESTION PATTERNS:")
    print(f"Old pattern (issue/task/comment): {old_pattern} documents")
    print(f"New pattern (public_issue/public_task): {new_pattern} documents")
    
    if old_pattern > 0 and new_pattern == 0:
        print("\n[INFO] Only old ingestion pattern found. The privacy-filtered ingestion may not have run successfully.")


if __name__ == "__main__":
    analyze_issue_ingestions()