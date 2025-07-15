"""Discover all training-related data types in Bubble.io"""
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def discover_training_data_types():
    """Search for all training-related data types in Bubble API"""
    
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
    
    # List of potential training-related data types to test
    # Based on common naming patterns and the training_data_pipeline.py expectations
    potential_types = [
        # Currently known
        "training",
        "TrainingModule", 
        
        # Expected from training_data_pipeline.py
        "trainingsession",
        "TrainingSession",
        "training_session",
        
        "trainingplan", 
        "TrainingPlan",
        "training_plan",
        "employeetrainingplan",
        "employee_training_plan",
        
        "trainingqualification",
        "TrainingQualification", 
        "training_qualification",
        
        "trainingattendance",
        "TrainingAttendance",
        "training_attendance",
        
        "trainingassessment",
        "TrainingAssessment",
        "training_assessment",
        
        "trainingfeedback",
        "TrainingFeedback",
        "training_feedback",
        
        # Other possibilities
        "trainee",
        "Trainee",
        "trainer", 
        "Trainer",
        "trainingcategory",
        "TrainingCategory",
        "training_category",
        "trainingrecord",
        "TrainingRecord",
        "training_record",
        "trainingcertificate",
        "TrainingCertificate",
        "training_certificate",
        "trainingschedule",
        "TrainingSchedule",
        "training_schedule",
        "trainingevent",
        "TrainingEvent",
        "training_event",
        "skill",
        "Skill",
        "competency",
        "Competency",
        "certification",
        "Certification"
    ]
    
    print("Searching for training-related data types in Bubble.io...")
    print(f"Testing {len(potential_types)} potential data type names")
    print("-" * 60)
    
    found_types = []
    training_data_summary = {}
    
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
                        
                        # Store summary
                        training_data_summary[data_type] = {
                            "count": count,
                            "fields": fields,
                            "sample": results[0] if results else {}
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
    print(f"SUMMARY: Found {len(found_types)} training-related data types")
    print("=" * 60)
    
    if found_types:
        print("\nAvailable training data types:")
        for dt in found_types:
            print(f"  - {dt} ({training_data_summary[dt]['count']} records)")
        
        # Save detailed findings
        with open("training_data_discovery.json", "w") as f:
            json.dump({
                "found_types": found_types,
                "summary": training_data_summary
            }, f, indent=2, default=str)
        print(f"\nDetailed findings saved to: training_data_discovery.json")
        
        # Analyze relationships
        print("\nAnalyzing relationships between training data types...")
        for data_type, info in training_data_summary.items():
            related_fields = [f for f in info['fields'] if 'training' in f.lower() or 'session' in f.lower() or 'module' in f.lower()]
            if related_fields:
                print(f"\n{data_type} has relationships via: {', '.join(related_fields)}")
    
    return found_types, training_data_summary


if __name__ == "__main__":
    found_types, summary = discover_training_data_types()