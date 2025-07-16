"""Discover all issue-related data types in Bubble.io"""
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def discover_issue_data_types():
    """Search for all issue-related data types in Bubble API"""
    
    app_url = os.environ.get("BUBBLE_APP_URL", "")
    api_token = os.environ.get("BUBBLE_API_TOKEN", "")
    
    if not app_url or not api_token:
        print("Missing Bubble.io configuration!")
        return
    
    base_url = f"{app_url.rstrip('/')}/api/1.1/obj"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # List of potential issue-related data types to test
    potential_types = [
        # Most likely names
        "issue",
        "Issue",
        "issues",
        "Issues",
        
        # Related to issues
        "ticket",
        "Ticket",
        "support",
        "Support",
        "supportticket",
        "SupportTicket",
        "support_ticket",
        
        # Bug/problem tracking
        "bug",
        "Bug",
        "problem",
        "Problem",
        "incident",
        "Incident",
        
        # Task/request related
        "task",
        "Task",
        "request",
        "Request",
        "servicerequest",
        "ServiceRequest",
        "service_request",
        
        # Feedback/complaint
        "feedback",
        "Feedback",
        "complaint",
        "Complaint",
        "report",
        "Report",
        
        # Issue tracking fields
        "issuestatus",
        "IssueStatus",
        "issue_status",
        "issuecategory",
        "IssueCategory",
        "issue_category",
        "issuetype",
        "IssueType",
        "issue_type",
        "issuepriority",
        "IssuePriority",
        "issue_priority",
        
        # Comments/notes (already found but might be issue-related)
        "comment",
        "Comment",
        "CommentThread",
        "commentthread",
        
        # Resolution/action
        "resolution",
        "Resolution",
        "action",
        "Action",
        "issueresolution",
        "IssueResolution",
        "issue_resolution"
    ]
    
    print("Searching for issue-related data types in Bubble.io...")
    print(f"Testing {len(potential_types)} potential data type names")
    print("-" * 60)
    
    found_types = []
    issue_data_summary = {}
    
    for data_type in potential_types:
        try:
            response = requests.get(
                f"{base_url}/{data_type}",
                headers=headers,
                params={"limit": 5},  # Get a few records to see structure
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                count = data.get("response", {}).get("count", 0)
                results = data.get("response", {}).get("results", [])
                
                if count > 0:
                    print(f"[FOUND] {data_type:<30} - {count} records")
                    found_types.append(data_type)
                    
                    # Analyze fields
                    if results:
                        fields = list(results[0].keys())
                        print(f"        Fields: {', '.join(fields[:8])}{'...' if len(fields) > 8 else ''}")
                        
                        # Look for issue-related fields
                        issue_fields = [f for f in fields if any(term in f.lower() for term in ['issue', 'ticket', 'status', 'priority', 'assign', 'resolve', 'category', 'type'])]
                        if issue_fields:
                            print(f"        Issue-related fields: {', '.join(issue_fields)}")
                        
                        # Store summary
                        issue_data_summary[data_type] = {
                            "count": count,
                            "fields": fields,
                            "sample": results[0] if results else {},
                            "issue_fields": issue_fields
                        }
                    print()
                    
            elif response.status_code == 404:
                # Silently skip - not found
                pass
            else:
                print(f"[ERROR] {data_type:<30} - Status {response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] {data_type:<30} - {str(e)[:50]}")
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: Found {len(found_types)} issue-related data types")
    print("=" * 60)
    
    if found_types:
        print("\nAvailable issue-related data types:")
        for dt in found_types:
            print(f"  - {dt} ({issue_data_summary[dt]['count']} records)")
            if issue_data_summary[dt]['issue_fields']:
                print(f"    Issue fields: {', '.join(issue_data_summary[dt]['issue_fields'])}")
        
        # Save detailed findings
        with open("issue_data_discovery.json", "w") as f:
            json.dump({
                "found_types": found_types,
                "summary": issue_data_summary
            }, f, indent=2, default=str)
        print(f"\nDetailed findings saved to: issue_data_discovery.json")
        
        # Analyze relationships
        print("\nAnalyzing relationships between issue data types...")
        for data_type, info in issue_data_summary.items():
            related_fields = [f for f in info['fields'] if any(term in f.lower() for term in ['issue', 'comment', 'thread', 'user', 'assign', 'created', 'modified'])]
            if related_fields:
                print(f"\n{data_type} has relationships via: {', '.join(related_fields)}")
    
    return found_types, issue_data_summary


if __name__ == "__main__":
    found_types, summary = discover_issue_data_types()