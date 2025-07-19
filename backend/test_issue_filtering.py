"""Test script to verify issue filtering is working correctly"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from langchain_core.runnables import RunnableConfig
from retrieval import make_retriever
from configuration import BaseConfiguration

# Load environment variables
load_dotenv()

async def test_issue_filtering():
    """Test filtering for issues with different configurations"""
    
    print("Testing Issue Filtering")
    print("=" * 60)
    
    # Test configurations
    test_configs = [
        {
            "name": "Filter by source_type=issue only",
            "search_kwargs": {
                "filter": {"source_type": "issue"},
                "k": 5
            }
        },
        {
            "name": "Filter by source_type=issue and category=1x9",
            "search_kwargs": {
                "filter": {
                    "source_type": "issue",
                    "category": "1x9"
                },
                "k": 5
            }
        },
        {
            "name": "No filter (baseline)",
            "search_kwargs": {
                "k": 5
            }
        }
    ]
    
    for test_config in test_configs:
        print(f"\n\nTest: {test_config['name']}")
        print("-" * 40)
        
        # Create configuration
        config = RunnableConfig(
            configurable={
                "search_kwargs": test_config["search_kwargs"]
            }
        )
        
        try:
            # Create retriever
            with make_retriever(config) as retriever:
                # Test query
                query = "Show me some issues"
                print(f"Query: {query}")
                print(f"Search kwargs: {test_config['search_kwargs']}")
                
                # Retrieve documents
                documents = await retriever.ainvoke(query)
                
                print(f"\nRetrieved {len(documents)} documents:")
                
                # Analyze results
                source_types = {}
                categories = {}
                
                for i, doc in enumerate(documents):
                    source_type = doc.metadata.get('source_type', 'N/A')
                    category = doc.metadata.get('category', 'N/A')
                    title = doc.metadata.get('title', 'N/A')
                    
                    # Count source types
                    source_types[source_type] = source_types.get(source_type, 0) + 1
                    
                    # Count categories
                    categories[category] = categories.get(category, 0) + 1
                    
                    print(f"  {i+1}. source_type={source_type}, category={category}, title={title[:50]}...")
                
                # Summary
                print(f"\nSource Type Distribution:")
                for st, count in source_types.items():
                    print(f"  {st}: {count}")
                
                print(f"\nCategory Distribution:")
                for cat, count in categories.items():
                    print(f"  {cat}: {count}")
                    
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Main function"""
    await test_issue_filtering()

if __name__ == "__main__":
    asyncio.run(main())