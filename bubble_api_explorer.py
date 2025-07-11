#!/usr/bin/env python3
"""
Bubble.io API Explorer
Connects to Bubble.io Data API to analyze data structure and content quality
for vector database integration planning.
"""

import requests
import json
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

class BubbleAPIExplorer:
    def __init__(self, app_url: str, api_token: str):
        """
        Initialize Bubble API Explorer
        
        Args:
            app_url: Your Bubble app URL (e.g., "https://app.bali.love")
            api_token: Your Bubble API private key
        """
        self.app_url = app_url.rstrip('/')
        self.api_token = api_token
        self.base_url = f"{self.app_url}/api/1.1/obj"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # Data types to explore (based on schema analysis)
        self.priority_data_types = [
            "event", "product", "venue", "comment", "eventreview",
            "booking", "guest", "vendor", "flow"
        ]
        
        self.exploration_results = {}
    
    def test_connection(self) -> bool:
        """Test API connection and authentication"""
        try:
            # Try to access a simple endpoint
            response = requests.get(f"{self.base_url}/event", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                print("✅ API connection successful!")
                return True
            elif response.status_code == 401:
                print("❌ Authentication failed. Please check your API token.")
                return False
            elif response.status_code == 404:
                print("⚠️  Event endpoint not found. Checking other endpoints...")
                return self._test_alternative_endpoints()
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def _test_alternative_endpoints(self) -> bool:
        """Test alternative endpoints if 'event' doesn't exist"""
        test_endpoints = ["booking", "guest", "product", "venue", "comment"]
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(f"{self.base_url}/{endpoint}", 
                                      headers=self.headers, timeout=10)
                if response.status_code == 200:
                    print(f"✅ Found working endpoint: {endpoint}")
                    return True
            except:
                continue
        
        print("❌ No working endpoints found.")
        return False
    
    def discover_available_endpoints(self) -> List[str]:
        """Discover which data type endpoints are actually available"""
        available_endpoints = []
        
        print("🔍 Discovering available endpoints...")
        
        for data_type in self.priority_data_types:
            try:
                response = requests.get(
                    f"{self.base_url}/{data_type}",
                    headers=self.headers,
                    params={"limit": 1},  # Just get 1 record to test
                    timeout=10
                )
                
                if response.status_code == 200:
                    available_endpoints.append(data_type)
                    print(f"  ✅ {data_type}")
                elif response.status_code == 404:
                    print(f"  ❌ {data_type} (not found)")
                else:
                    print(f"  ⚠️  {data_type} (status: {response.status_code})")
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ {data_type} (error: {e})")
        
        return available_endpoints
    
    def sample_data_type(self, data_type: str, sample_size: int = 5) -> Optional[Dict]:
        """Sample data from a specific data type"""
        try:
            print(f"📊 Sampling {data_type} data...")
            
            response = requests.get(
                f"{self.base_url}/{data_type}",
                headers=self.headers,
                params={"limit": sample_size},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'response' in data and 'results' in data['response']:
                    results = data['response']['results']
                    count = data['response'].get('count', 0)
                    
                    print(f"  📝 Found {count} records, sampled {len(results)}")
                    
                    return {
                        'data_type': data_type,
                        'total_count': count,
                        'sample_size': len(results),
                        'sample_data': results,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    print(f"  ⚠️  Unexpected response format for {data_type}")
                    return None
            else:
                print(f"  ❌ Failed to sample {data_type}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ❌ Error sampling {data_type}: {e}")
            return None
    
    def analyze_field_structure(self, sample_data: List[Dict]) -> Dict:
        """Analyze the field structure of sampled data"""
        if not sample_data:
            return {}
        
        field_analysis = {}
        
        for record in sample_data:
            for field_name, field_value in record.items():
                if field_name not in field_analysis:
                    field_analysis[field_name] = {
                        'type': type(field_value).__name__,
                        'sample_values': [],
                        'non_empty_count': 0,
                        'avg_length': 0,
                        'is_rich_text': False
                    }
                
                if field_value is not None and field_value != "":
                    field_analysis[field_name]['non_empty_count'] += 1
                    field_analysis[field_name]['sample_values'].append(str(field_value)[:100])
                    
                    # Check if this looks like rich text content
                    if isinstance(field_value, str) and len(field_value) > 50:
                        field_analysis[field_name]['is_rich_text'] = True
                        field_analysis[field_name]['avg_length'] = (
                            field_analysis[field_name]['avg_length'] + len(field_value)
                        ) / 2
        
        # Keep only top 3 sample values for each field
        for field in field_analysis:
            field_analysis[field]['sample_values'] = field_analysis[field]['sample_values'][:3]
        
        return field_analysis
    
    def identify_vector_candidates(self, field_analysis: Dict) -> List[Dict]:
        """Identify fields that are good candidates for vectorization"""
        candidates = []
        
        for field_name, field_info in field_analysis.items():
            # Skip system fields
            if field_name.lower() in ['_id', 'created_date', 'modified_date', 'created_by']:
                continue
            
            # Calculate a "richness score"
            richness_score = 0
            
            if field_info['is_rich_text']:
                richness_score += 3
            
            if field_info['avg_length'] > 100:
                richness_score += 2
            elif field_info['avg_length'] > 50:
                richness_score += 1
            
            if field_info['non_empty_count'] > 0:
                richness_score += 1
            
            # Look for keywords that suggest rich content
            field_lower = field_name.lower()
            if any(keyword in field_lower for keyword in 
                   ['description', 'content', 'text', 'detail', 'note', 'comment', 'review']):
                richness_score += 2
            
            if richness_score >= 3:  # Threshold for vector candidates
                candidates.append({
                    'field_name': field_name,
                    'richness_score': richness_score,
                    'avg_length': field_info['avg_length'],
                    'sample_content': field_info['sample_values'][0] if field_info['sample_values'] else ""
                })
        
        return sorted(candidates, key=lambda x: x['richness_score'], reverse=True)
    
    def explore_all_priority_types(self) -> Dict:
        """Explore all priority data types and analyze them"""
        print("🚀 Starting comprehensive exploration...")
        
        if not self.test_connection():
            return {}
        
        available_endpoints = self.discover_available_endpoints()
        
        if not available_endpoints:
            print("❌ No available endpoints found. Please check your API configuration.")
            return {}
        
        exploration_results = {}
        
        for data_type in available_endpoints:
            print(f"\n🔍 Exploring {data_type}...")
            
            sample_result = self.sample_data_type(data_type)
            if sample_result:
                field_analysis = self.analyze_field_structure(sample_result['sample_data'])
                vector_candidates = self.identify_vector_candidates(field_analysis)
                
                exploration_results[data_type] = {
                    'sample_info': sample_result,
                    'field_analysis': field_analysis,
                    'vector_candidates': vector_candidates
                }
                
                print(f"  📋 Fields analyzed: {len(field_analysis)}")
                print(f"  🎯 Vector candidates: {len(vector_candidates)}")
                
                if vector_candidates:
                    print(f"  🏆 Top candidate: {vector_candidates[0]['field_name']}")
        
        self.exploration_results = exploration_results
        return exploration_results
    
    def generate_integration_report(self) -> str:
        """Generate a comprehensive integration report"""
        if not self.exploration_results:
            return "No exploration results available. Run explore_all_priority_types() first."
        
        report_lines = [
            "# Bubble.io Integration Analysis Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"App URL: {self.app_url}",
            "\n## Executive Summary"
        ]
        
        total_records = sum(
            result['sample_info']['total_count'] 
            for result in self.exploration_results.values()
        )
        
        total_vector_candidates = sum(
            len(result['vector_candidates'])
            for result in self.exploration_results.values()
        )
        
        report_lines.extend([
            f"- **Data Types Analyzed**: {len(self.exploration_results)}",
            f"- **Total Records**: {total_records:,}",
            f"- **Vector-Ready Fields**: {total_vector_candidates}",
            "\n## Data Type Analysis"
        ])
        
        for data_type, results in self.exploration_results.items():
            sample_info = results['sample_info']
            candidates = results['vector_candidates']
            
            report_lines.extend([
                f"\n### {data_type.title()}",
                f"- **Total Records**: {sample_info['total_count']:,}",
                f"- **Vector Candidates**: {len(candidates)}"
            ])
            
            if candidates:
                report_lines.append("- **Top Fields for Vectorization**:")
                for candidate in candidates[:3]:  # Top 3
                    report_lines.append(
                        f"  - `{candidate['field_name']}` (score: {candidate['richness_score']}, "
                        f"avg length: {int(candidate['avg_length'])})"
                    )
                    if candidate['sample_content']:
                        preview = candidate['sample_content'][:100] + "..." if len(candidate['sample_content']) > 100 else candidate['sample_content']
                        report_lines.append(f"    - Preview: \"{preview}\"")
        
        report_lines.extend([
            "\n## Integration Recommendations",
            "\n### Phase 1: High-Value Content",
            "Start with these data types that have rich, searchable content:"
        ])
        
        # Sort data types by number of vector candidates
        sorted_types = sorted(
            self.exploration_results.items(),
            key=lambda x: len(x[1]['vector_candidates']),
            reverse=True
        )
        
        for data_type, results in sorted_types[:5]:  # Top 5
            count = results['sample_info']['total_count']
            candidates = len(results['vector_candidates'])
            report_lines.append(f"- **{data_type.title()}**: {count:,} records, {candidates} vector fields")
        
        report_lines.extend([
            "\n### Phase 2: Implementation Strategy",
            "1. **Start Small**: Begin with Event and Product data types",
            "2. **Field Mapping**: Focus on description and content fields",
            "3. **Metadata Extraction**: Include dates, categories, and relationships",
            "4. **Incremental Updates**: Set up daily/hourly sync based on update frequency",
            "5. **Quality Monitoring**: Track ingestion success and content quality"
        ])
        
        return "\n".join(report_lines)
    
    def save_results(self, filename: str = "bubble_exploration_results.json"):
        """Save exploration results to JSON file"""
        if self.exploration_results:
            with open(filename, 'w') as f:
                json.dump(self.exploration_results, f, indent=2, default=str)
            print(f"💾 Results saved to {filename}")

def main():
    """Main exploration function"""
    print("🔮 Bubble.io API Explorer")
    print("=" * 50)
    
    # Configuration
    app_url = input("Enter your Bubble app URL (e.g., https://app.bali.love): ").strip()
    api_token = input("Enter your Bubble API private key: ").strip()
    
    if not app_url or not api_token:
        print("❌ Both app URL and API token are required.")
        return
    
    # Initialize explorer
    explorer = BubbleAPIExplorer(app_url, api_token)
    
    # Run exploration
    results = explorer.explore_all_priority_types()
    
    if results:
        # Generate and save report
        report = explorer.generate_integration_report()
        
        # Save results
        explorer.save_results()
        
        # Save report
        with open("bubble_integration_report.md", "w") as f:
            f.write(report)
        
        print("\n" + "=" * 50)
        print("🎉 Exploration Complete!")
        print("📄 Report saved to: bubble_integration_report.md")
        print("💾 Raw data saved to: bubble_exploration_results.json")
        print("\n📋 Quick Summary:")
        
        for data_type, result in list(results.items())[:3]:
            count = result['sample_info']['total_count']
            candidates = len(result['vector_candidates'])
            print(f"  • {data_type}: {count:,} records, {candidates} vector fields")
    
    else:
        print("❌ Exploration failed. Please check your API configuration.")

if __name__ == "__main__":
    main() 