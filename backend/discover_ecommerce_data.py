"""Discover e-commerce data types (products, vendors, venues) in Bubble.io"""
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def discover_ecommerce_data_types():
    """Search for all e-commerce related data types in Bubble API"""
    
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
    
    # E-commerce data types to check
    ecommerce_types = [
        # Products
        "product", "Product",
        "productimage", "ProductImage", 
        "productsatellite", "ProductSatellite",
        "productcategory", "ProductCategory",
        "service", "Service",
        
        # Vendors
        "vendor", "Vendor",
        "vendorimage", "VendorImage",
        "vendorcategory", "VendorCategory",
        "supplier", "Supplier",
        
        # Venues
        "venue", "Venue",
        "venueimage", "VenueImage",
        "venuecategory", "VenueCategory",
        "location", "Location",
        
        # Related
        "booking", "Booking",
        "package", "Package",
        "pricing", "Pricing",
        "availability", "Availability"
    ]
    
    print("Searching for e-commerce data types in Bubble.io...")
    print(f"Testing {len(ecommerce_types)} potential data type names")
    print("-" * 60)
    
    found_types = []
    ecommerce_summary = {}
    
    for data_type in ecommerce_types:
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
                    print(f"[FOUND] {data_type:<30} - {count} records")
                    found_types.append(data_type)
                    
                    # Analyze fields
                    if results:
                        fields = list(results[0].keys())
                        print(f"        Key fields: {', '.join(fields[:10])}{'...' if len(fields) > 10 else ''}")
                        
                        # Look for important e-commerce fields
                        commerce_fields = [f for f in fields if any(term in f.lower() for term in 
                                         ['price', 'cost', 'name', 'description', 'category', 'image', 
                                          'status', 'publish', 'feature', 'location', 'capacity'])]
                        if commerce_fields:
                            print(f"        Commerce fields: {', '.join(commerce_fields)}")
                        
                        # Store summary
                        ecommerce_summary[data_type] = {
                            "count": count,
                            "fields": fields,
                            "sample": results[0] if results else {},
                            "commerce_fields": commerce_fields
                        }
                    print()
                    
            elif response.status_code == 404:
                pass  # Not found - skip silently
            else:
                print(f"[ERROR] {data_type:<30} - Status {response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] {data_type:<30} - {str(e)[:50]}")
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: Found {len(found_types)} e-commerce data types")
    print("=" * 60)
    
    # Group by category
    products = [t for t in found_types if 'product' in t.lower()]
    vendors = [t for t in found_types if 'vendor' in t.lower()]
    venues = [t for t in found_types if 'venue' in t.lower()]
    others = [t for t in found_types if t.lower() not in str(products + vendors + venues).lower()]
    
    if products:
        print(f"\nPRODUCT TYPES ({len(products)}):")
        for dt in products:
            print(f"  - {dt} ({ecommerce_summary[dt]['count']} records)")
    
    if vendors:
        print(f"\nVENDOR TYPES ({len(vendors)}):")
        for dt in vendors:
            print(f"  - {dt} ({ecommerce_summary[dt]['count']} records)")
    
    if venues:
        print(f"\nVENUE TYPES ({len(venues)}):")
        for dt in venues:
            print(f"  - {dt} ({ecommerce_summary[dt]['count']} records)")
    
    if others:
        print(f"\nOTHER TYPES ({len(others)}):")
        for dt in others:
            print(f"  - {dt} ({ecommerce_summary[dt]['count']} records)")
    
    # Save findings
    if found_types:
        with open("ecommerce_data_discovery.json", "w") as f:
            json.dump({
                "found_types": found_types,
                "summary": ecommerce_summary,
                "categories": {
                    "products": products,
                    "vendors": vendors,
                    "venues": venues,
                    "others": others
                }
            }, f, indent=2, default=str)
        print(f"\nDetailed findings saved to: ecommerce_data_discovery.json")
    
    return found_types, ecommerce_summary


if __name__ == "__main__":
    found_types, summary = discover_ecommerce_data_types()