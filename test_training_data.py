#!/usr/bin/env python3
"""
Test script to explore your Bubble.io training data and build realistic LangSmith datasets.

This script helps you:
1. Connect to your Bubble.io training data
2. Understand what data you actually have
3. Identify potential duplicates in your real content
4. Generate sample queries for LangSmith datasets
"""

import os
import sys
from typing import Dict, List, Set
from collections import defaultdict, Counter

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from bubble_loader import load_bubble_data, BubbleConfig, BubbleSyncManager, BubbleDataLoader
except ImportError as e:
    print(f"Error importing bubble_loader: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def analyze_training_data():
    """Analyze your actual training data to understand structure and content"""
    print("🔍 ANALYZING YOUR BUBBLE.IO TRAINING DATA")
    print("=" * 50)
    
    # Load data
    print("Loading data from Bubble.io...")
    docs = load_bubble_data()
    
    if not docs:
        print("❌ No data found. Please check:")
        print("   1. Environment variables are set (BUBBLE_APP_URL, BUBBLE_API_TOKEN)")
        print("   2. Your Bubble.io app has training data types")
        print("   3. API permissions are enabled")
        print("\nSee BUBBLE_SETUP.md for configuration help.")
        return
    
    print(f"✅ Successfully loaded {len(docs)} documents")
    print()
    
    # Analyze by data type
    data_types = defaultdict(list)
    for doc in docs:
        data_type = doc.metadata.get('data_type', 'unknown')
        data_types[data_type].append(doc)
    
    print("📊 DATA BREAKDOWN BY TYPE:")
    print("-" * 30)
    training_data_found = False
    for data_type, docs_list in data_types.items():
        print(f"  {data_type}: {len(docs_list)} records")
        if data_type.startswith('training_'):
            training_data_found = True
    
    if not training_data_found:
        print("\n⚠️  No training data types found!")
        print("Expected: training_module, training_session, employee_training_plan, etc.")
        print("Check your Bubble.io data type names.")
        return
    
    print()
    
    # Analyze training modules for duplicates
    analyze_potential_duplicates(data_types)
    
    # Show sample content
    show_sample_content(data_types)
    
    # Generate realistic queries
    generate_sample_queries(data_types)


def analyze_potential_duplicates(data_types: Dict[str, List]) -> None:
    """Analyze training modules for potential duplicate content"""
    if 'training_module' not in data_types:
        print("ℹ️  No training_module data found - skipping duplicate analysis")
        return
    
    print("🔍 ANALYZING FOR POTENTIAL DUPLICATES:")
    print("-" * 40)
    
    modules = data_types['training_module']
    print(f"Analyzing {len(modules)} training modules...")
    
    # Group by similar titles
    title_groups = defaultdict(list)
    for doc in modules:
        content = doc.page_content.lower()
        # Extract title from content
        lines = content.split('\n')
        title_line = lines[0] if lines else 'untitled'
        if 'training module:' in title_line:
            title = title_line.replace('training module:', '').strip()
        else:
            title = title_line[:50]  # First 50 chars
        
        # Group similar titles
        title_groups[title].append(doc)
    
    # Find potential duplicates
    duplicates_found = False
    for title, docs_with_title in title_groups.items():
        if len(docs_with_title) > 1:
            duplicates_found = True
            print(f"\n🔄 Potential duplicates found for: '{title}'")
            for i, doc in enumerate(docs_with_title):
                preview = doc.page_content[:100].replace('\n', ' ')
                print(f"   Version {i+1}: {preview}...")
    
    if not duplicates_found:
        print("✅ No obvious duplicate titles found")
        
        # Check for similar content
        print("\n🔍 Checking for similar content...")
        similar_content = find_similar_content(modules)
        if similar_content:
            print("⚠️  Found potentially similar content:")
            for pair in similar_content[:3]:  # Show top 3
                doc1, doc2, similarity = pair
                print(f"   Similarity {similarity:.1%} between modules")
                print(f"   Module 1: {doc1.page_content[:60]}...")
                print(f"   Module 2: {doc2.page_content[:60]}...")
                print()
        else:
            print("✅ No similar content detected")


def find_similar_content(modules: List) -> List:
    """Find modules with similar content using simple text similarity"""
    similar_pairs = []
    
    for i, doc1 in enumerate(modules):
        for j, doc2 in enumerate(modules[i+1:], i+1):
            # Simple similarity check
            content1 = set(doc1.page_content.lower().split())
            content2 = set(doc2.page_content.lower().split())
            
            if len(content1) == 0 or len(content2) == 0:
                continue
                
            intersection = len(content1.intersection(content2))
            union = len(content1.union(content2))
            similarity = intersection / union if union > 0 else 0
            
            if similarity > 0.7:  # 70% similarity threshold
                similar_pairs.append((doc1, doc2, similarity))
    
    return sorted(similar_pairs, key=lambda x: x[2], reverse=True)


def show_sample_content(data_types: Dict[str, List]) -> None:
    """Show sample content from each training data type"""
    print("📝 SAMPLE CONTENT BY TYPE:")
    print("-" * 30)
    
    for data_type, docs_list in data_types.items():
        if data_type.startswith('training_') and docs_list:
            print(f"\n📋 {data_type.replace('_', ' ').title()}:")
            sample_doc = docs_list[0]
            preview = sample_doc.page_content[:200].replace('\n', ' ')
            print(f"   {preview}...")
            
            # Show metadata
            metadata = sample_doc.metadata
            print(f"   Metadata: {list(metadata.keys())}")


def generate_sample_queries(data_types: Dict[str, List]) -> None:
    """Generate sample queries based on your actual training data"""
    print("\n💡 SAMPLE QUERIES FOR YOUR TRAINING DATA:")
    print("-" * 45)
    
    queries = []
    
    # Duplicate analysis queries
    if 'training_module' in data_types:
        modules = data_types['training_module']
        if len(modules) > 1:
            queries.extend([
                "Review all training modules and identify any duplicate or overlapping content",
                "Which training modules cover similar topics and could be consolidated?",
                "Check for redundant training materials that should be merged"
            ])
    
    # Scheduling queries  
    if 'training_session' in data_types and 'employee_training_plan' in data_types:
        queries.extend([
            "Who needs training sessions scheduled this week?",
            "List employees with upcoming training deadlines",
            "Which training sessions have low enrollment and need promotion?"
        ])
    
    # Compliance queries
    if 'training_attendance' in data_types:
        queries.extend([
            "Which employees haven't completed required compliance training?",
            "Generate a compliance report for employees overdue on training",
            "Who needs to retake assessments due to low scores?"
        ])
    
    # Content review queries
    if any(dt in data_types for dt in ['training_feedback', 'training_assessment']):
        queries.extend([
            "Which training modules have consistently low ratings?",
            "Analyze feedback to identify training content that needs updating",
            "What improvements are suggested most frequently for our training programs?"
        ])
    
    for i, query in enumerate(queries[:6], 1):  # Show top 6
        print(f"   {i}. {query}")
    
    print(f"\n🎯 These {len(queries)} sample queries are based on your actual data types!")
    print("   Use these to create realistic LangSmith datasets.")


def main():
    print("🚀 TRAINING DATA EXPLORATION TOOL")
    print("This tool analyzes your actual Bubble.io training data")
    print("and helps build realistic LangSmith datasets.\n")
    
    # Check environment
    required_vars = ['BUBBLE_APP_URL', 'BUBBLE_API_TOKEN']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("⚠️  Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease check BUBBLE_SETUP.md for configuration instructions.")
        return
    
    try:
        analyze_training_data()
    except Exception as e:
        print(f"❌ Error analyzing data: {e}")
        print("\nCheck your Bubble.io configuration and try again.")


if __name__ == "__main__":
    main() 