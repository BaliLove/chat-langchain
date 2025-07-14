"""Discover all available Bubble data types"""

import os
import requests
from dotenv import load_dotenv
import json
import time

# Load environment
load_dotenv()

def discover_bubble_datatypes():
    """Try to discover all available data types in Bubble"""
    
    api_token = os.getenv("BUBBLE_API_TOKEN")
    if not api_token:
        print("[ERROR] BUBBLE_API_TOKEN not found")
        return
    
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # We found that User works, so let's use the same pattern
    base_url = "https://app.bali.love/api/1.1/obj/"
    
    print("=== Discovering Bubble Data Types ===\n")
    
    # Based on the schema analysis, let's test these systematically
    # Using exact names from bubble_schema_analysis.md
    test_datatypes = [
        # Core Event Management (from schema)
        "Event", "EventReview", "EventRSVP", "EventSatellite", "EventLoad", "RefEvent", "PreEvent",
        
        # Booking & Reservations
        "Booking", "BookingGuests", "BookingGuestHouse", "AutomationBookingCondition", 
        "Cabana", "CabanaType",
        
        # User & Guest Management
        "Guest", "GuestList", "GuestEvent", "GuestRedition", "GuestSetting", 
        "Teammate", "RouteTeam",
        
        # Communication & Messaging
        "Comment", "CommentReaction", "CommentExtended", "CommentThread",
        "InboxConversation", "InboxConversationUser", "InboxPFMessaggi", "AutomationMessagequeue",
        
        # Payments & Transactions
        "Payment", "Payroll", "TransactionDelay", "TransactionTask",
        
        # Products & Inventory
        "Product", "ProductLinks", "ProductImage", "ProductConference", "ProductSatellite",
        "ProductAutocompleteCategory",
        
        # Venue & Location Management
        "Venue", "VenueImage", "VenueSchedule", "Vendor", "VendorImage",
        
        # Try lowercase versions too
        "event", "venue", "product", "booking", "guest", "payment",
        
        # Some alternatives based on common patterns
        "events", "venues", "products", "bookings", "guests", "payments",
        
        # Training related (might exist)
        "Training", "training", "TrainingModule", "training_module"
    ]
    
    working_datatypes = {}
    
    for datatype in test_datatypes:
        url = f"{base_url}{datatype}"
        
        try:
            response = requests.get(url, headers=headers, params={"limit": 1})
            
            if response.status_code == 200:
                data = response.json()
                resp = data.get("response", {})
                
                if isinstance(resp, dict):
                    count = resp.get("count", 0)
                    results = resp.get("results", [])
                    
                    if count > 0 or results:
                        print(f"[OK] {datatype}: Found {count} total records")
                        working_datatypes[datatype] = {
                            "count": count,
                            "sample_fields": list(results[0].keys()) if results else []
                        }
                        
                        # Show sample fields
                        if results:
                            fields = list(results[0].keys())[:8]
                            print(f"     Fields: {', '.join(fields)}...")
                            
            elif response.status_code != 404:
                print(f"[INFO] {datatype}: Status {response.status_code}")
                
            # Small delay to avoid rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            print(f"[ERROR] {datatype}: {e}")
    
    print(f"\n=== Summary ===")
    print(f"Found {len(working_datatypes)} working data types")
    
    # Save discovered datatypes
    if working_datatypes:
        with open("bubble_datatypes.json", "w") as f:
            json.dump({
                "base_url": base_url,
                "datatypes": working_datatypes,
                "discovered_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
        print(f"Saved to bubble_datatypes.json")
    
    # Show detailed analysis of interesting datatypes
    print("\n=== Detailed Analysis ===")
    
    interesting_types = ["Event", "event", "Venue", "venue", "Product", "product", 
                        "Booking", "booking", "Guest", "guest"]
    
    for datatype in interesting_types:
        if datatype in working_datatypes:
            print(f"\n{datatype} ({working_datatypes[datatype]['count']} records):")
            
            # Get a few records to analyze
            url = f"{base_url}{datatype}"
            try:
                response = requests.get(url, headers=headers, params={"limit": 3})
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("response", {}).get("results", [])
                    
                    if results:
                        # Analyze field patterns
                        all_fields = set()
                        text_fields = []
                        
                        for record in results:
                            all_fields.update(record.keys())
                            
                            # Find text fields with content
                            for field, value in record.items():
                                if isinstance(value, str) and len(value) > 50:
                                    if field not in text_fields:
                                        text_fields.append(field)
                        
                        print(f"  Total fields: {len(all_fields)}")
                        print(f"  Text fields: {', '.join(text_fields[:5])}")
                        
                        # Show sample record
                        print(f"  Sample record:")
                        sample = results[0]
                        for key, value in list(sample.items())[:10]:
                            if value:
                                value_str = str(value)[:60] + "..." if len(str(value)) > 60 else str(value)
                                print(f"    {key}: {value_str}")
                                
            except Exception as e:
                print(f"  Error getting details: {e}")


if __name__ == "__main__":
    discover_bubble_datatypes()