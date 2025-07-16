"""Discover all event-related data types in Bubble.io for comprehensive event ecosystem"""
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def discover_event_ecosystem():
    """Search for all event-related data types in Bubble API"""
    
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
    
    # Comprehensive list of event-related data types
    event_types = [
        # Core event types
        "event", "Event",
        "events", "Events",
        
        # Event components
        "eventsatellite", "EventSatellite",
        "eventreview", "EventReview",
        "eventrsvp", "EventRSVP",
        "eventtype", "EventType",
        "eventdetail", "EventDetail",
        "eventinfo", "EventInfo",
        
        # Guest/Contact related
        "guest", "Guest",
        "guestlist", "GuestList", 
        "guestevent", "GuestEvent",
        "contact", "Contact",
        "client", "Client",
        "host", "Host",
        
        # Communication
        "message", "Message",
        "comment", "Comment",
        "commentthread", "CommentThread",
        "note", "Note",
        "eventnote", "EventNote",
        
        # Event logistics
        "timeline", "Timeline",
        "schedule", "Schedule",
        "agenda", "Agenda",
        "runsheet", "RunSheet",
        
        # Event data
        "leadinformation", "LeadInformation",
        "billing", "Billing",
        "invoice", "Invoice",
        "payment", "Payment",
        
        # Tasks and team
        "task", "Task",
        "eventtask", "EventTask",
        "team", "Team",
        "eventteam", "EventTeam",
        
        # Documents
        "document", "Document",
        "eventdocument", "EventDocument",
        "contract", "Contract"
    ]
    
    print("Discovering EVENT ECOSYSTEM in Bubble.io...")
    print(f"Testing {len(event_types)} potential data type names")
    print("-" * 80)
    
    found_types = []
    event_ecosystem = {}
    
    for data_type in event_types:
        try:
            response = requests.get(
                f"{base_url}/{data_type}",
                headers=headers,
                params={"limit": 5},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                count = data.get("response", {}).get("count", 0)
                results = data.get("response", {}).get("results", [])
                
                if count > 0:
                    print(f"\n[FOUND] {data_type:<30} - {count} records")
                    found_types.append(data_type)
                    
                    # Analyze fields
                    if results:
                        fields = list(results[0].keys())
                        
                        # Look for event relationships
                        event_fields = [f for f in fields if 'event' in f.lower()]
                        if event_fields:
                            print(f"  Event relationships: {', '.join(event_fields)}")
                        
                        # Look for important fields
                        key_fields = []
                        for f in fields:
                            f_lower = f.lower()
                            if any(term in f_lower for term in ['code', 'name', 'status', 'date', 'host', 'client', 'guest']):
                                key_fields.append(f)
                        
                        if key_fields:
                            print(f"  Key fields: {', '.join(key_fields[:8])}")
                        
                        # Show sample event code if present
                        sample = results[0]
                        if 'code' in sample:
                            print(f"  Sample code: {sample['code']}")
                        
                        # Store summary
                        event_ecosystem[data_type] = {
                            "count": count,
                            "fields": fields,
                            "event_fields": event_fields,
                            "key_fields": key_fields,
                            "sample": sample,
                            "has_event_reference": any('event' in f.lower() for f in fields)
                        }
                    
            elif response.status_code == 404:
                pass  # Not found
            else:
                print(f"[ERROR] {data_type:<30} - Status {response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] {data_type:<30} - {str(e)[:50]}")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: Found {len(found_types)} event-related data types")
    print("=" * 80)
    
    # Categorize findings
    core_event_types = [t for t in found_types if t.lower() in ['event', 'events']]
    guest_types = [t for t in found_types if 'guest' in t.lower() or 'contact' in t.lower() or 'client' in t.lower()]
    comm_types = [t for t in found_types if any(term in t.lower() for term in ['comment', 'message', 'note'])]
    task_types = [t for t in found_types if 'task' in t.lower()]
    
    # Show types that have event references
    event_linked = [(t, info) for t, info in event_ecosystem.items() if info['has_event_reference']]
    
    print(f"\nCORE EVENT TYPES:")
    for dt in core_event_types:
        info = event_ecosystem[dt]
        print(f"  - {dt} ({info['count']} records)")
        if 'code' in info['fields']:
            print(f"    HAS EVENT CODE FIELD [YES]")
    
    print(f"\nTYPES WITH EVENT REFERENCES ({len(event_linked)}):")
    for dt, info in event_linked:
        print(f"  - {dt}: {', '.join(info['event_fields'])}")
    
    if guest_types:
        print(f"\nGUEST/CONTACT TYPES:")
        for dt in guest_types:
            print(f"  - {dt} ({event_ecosystem[dt]['count']} records)")
    
    if comm_types:
        print(f"\nCOMMUNICATION TYPES:")
        for dt in comm_types:
            print(f"  - {dt} ({event_ecosystem[dt]['count']} records)")
    
    # Save findings
    with open("event_ecosystem_discovery.json", "w") as f:
        json.dump({
            "found_types": found_types,
            "ecosystem": event_ecosystem,
            "categories": {
                "core_events": core_event_types,
                "guest_contact": guest_types,
                "communication": comm_types,
                "tasks": task_types,
                "event_linked": [t for t, _ in event_linked]
            }
        }, f, indent=2, default=str)
    
    print(f"\nDetailed findings saved to: event_ecosystem_discovery.json")
    
    # Analyze event code patterns
    print("\n" + "=" * 80)
    print("EVENT CODE ANALYSIS:")
    for dt in core_event_types:
        info = event_ecosystem[dt]
        if 'code' in info['fields'] and info['sample'].get('code'):
            print(f"\n{dt} code format: {info['sample']['code']}")
            print("This code can be used to filter all related data!")
    
    return found_types, event_ecosystem


if __name__ == "__main__":
    found_types, ecosystem = discover_event_ecosystem()