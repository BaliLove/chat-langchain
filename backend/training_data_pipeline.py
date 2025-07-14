"""Training data ingestion pipeline for Bubble.io → Supabase → Vector DB"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from backend.staged_ingestion_pipeline import StagedIngestionPipeline
from backend.supabase_client import get_supabase_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrainingDataPipeline(StagedIngestionPipeline):
    """Specialized pipeline for training data."""
    
    # Training data types we'll ingest
    TRAINING_DATA_TYPES = [
        "TrainingModule",
        "trainingsession", 
        "trainingplan",
        "trainingqualification",
        # These might not exist in Bubble yet:
        # "training_attendance",
        # "training_assessment",
        # "training_feedback"
    ]
    
    def __init__(self):
        super().__init__()
        self.bubble_api_url = "https://app.bali.love/api/1.1/obj/"
        self.bubble_api_token = None  # Set from environment
    
    async def fetch_training_data_from_bubble(self, data_type: str, 
                                            limit: int = 100, 
                                            cursor: int = 0) -> List[Dict[str, Any]]:
        """Fetch training data from Bubble API."""
        import aiohttp
        import os
        
        if not self.bubble_api_token:
            self.bubble_api_token = os.getenv("BUBBLE_API_TOKEN")
            
        if not self.bubble_api_token:
            raise ValueError("BUBBLE_API_TOKEN not set")
        
        headers = {
            "Authorization": f"Bearer {self.bubble_api_token}"
        }
        
        params = {
            "limit": limit,
            "cursor": cursor
        }
        
        url = f"{self.bubble_api_url}{data_type}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("response", {}).get("results", [])
                    else:
                        logger.error(f"Error fetching {data_type}: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching from Bubble: {e}")
            return []
    
    def process_training_module(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process training module data for staging."""
        # Extract all possible fields based on Bubble schema
        processed = {
            "id": raw_data.get("_id"),
            "title": raw_data.get("title") or raw_data.get("name") or raw_data.get("module_name", ""),
            "content": self._build_module_content(raw_data),
            "metadata": {
                "data_type": "training_module",
                "category": raw_data.get("category") or raw_data.get("training_category"),
                "duration": raw_data.get("duration"),
                "prerequisites": raw_data.get("prerequisites"),
                "learning_objectives": raw_data.get("learning_objectives"),
                "status": raw_data.get("status", "active"),
                "created_date": raw_data.get("Created Date"),
                "modified_date": raw_data.get("Modified Date"),
            }
        }
        
        # Clean up None values
        processed["metadata"] = {k: v for k, v in processed["metadata"].items() if v is not None}
        return processed
    
    def process_training_session(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process training session data."""
        processed = {
            "id": raw_data.get("_id"),
            "title": raw_data.get("session_name") or raw_data.get("title") or raw_data.get("name", ""),
            "content": self._build_session_content(raw_data),
            "metadata": {
                "data_type": "training_session",
                "training_module": raw_data.get("training_module"),
                "instructor": raw_data.get("instructor") or raw_data.get("trainer"),
                "date": raw_data.get("date") or raw_data.get("session_date"),
                "time": raw_data.get("time") or raw_data.get("session_time"),
                "location": raw_data.get("location") or raw_data.get("venue"),
                "capacity": raw_data.get("capacity") or raw_data.get("max_attendees"),
                "status": raw_data.get("status"),
            }
        }
        
        processed["metadata"] = {k: v for k, v in processed["metadata"].items() if v is not None}
        return processed
    
    def process_training_plan(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process training plan data."""
        employee_name = raw_data.get("employee_name") or raw_data.get("employee", "")
        
        processed = {
            "id": raw_data.get("_id"),
            "title": f"Training Plan for {employee_name}",
            "content": self._build_training_plan_content(raw_data),
            "metadata": {
                "data_type": "training_plan",
                "employee_name": employee_name,
                "employee_id": raw_data.get("employee_id"),
                "department": raw_data.get("department"),
                "role": raw_data.get("role") or raw_data.get("position"),
                "required_modules": raw_data.get("required_modules") or raw_data.get("training_modules"),
                "deadline": raw_data.get("completion_deadline") or raw_data.get("deadline"),
                "completion_status": raw_data.get("completion_status"),
                "manager": raw_data.get("manager") or raw_data.get("supervisor"),
            }
        }
        
        processed["metadata"] = {k: v for k, v in processed["metadata"].items() if v is not None}
        return processed
    
    def process_training_qualification(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process training qualification data."""
        processed = {
            "id": raw_data.get("_id"),
            "title": raw_data.get("name") or raw_data.get("qualification_name", ""),
            "content": self._build_qualification_content(raw_data),
            "metadata": {
                "data_type": "training_qualification",
                "description": raw_data.get("description"),
                "requirements": raw_data.get("requirements"),
                "valid_for": raw_data.get("valid_for") or raw_data.get("validity_period"),
                "category": raw_data.get("category") or raw_data.get("qualification_type"),
            }
        }
        
        processed["metadata"] = {k: v for k, v in processed["metadata"].items() if v is not None}
        return processed
    
    def process_training_attendance(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process training attendance data."""
        processed = {
            "id": raw_data.get("_id"),
            "title": f"Attendance: {raw_data.get('employee_name', '')} - {raw_data.get('training_session', '')}",
            "content": self._build_attendance_content(raw_data),
            "metadata": {
                "data_type": "training_attendance",
                "employee_name": raw_data.get("employee_name") or raw_data.get("employee"),
                "training_session": raw_data.get("training_session") or raw_data.get("session"),
                "attendance_status": raw_data.get("attendance_status") or raw_data.get("status"),
                "date": raw_data.get("date") or raw_data.get("attendance_date"),
                "check_in_time": raw_data.get("check_in_time"),
                "check_out_time": raw_data.get("check_out_time"),
            }
        }
        
        processed["metadata"] = {k: v for k, v in processed["metadata"].items() if v is not None}
        return processed
    
    def process_training_assessment(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process training assessment data."""
        processed = {
            "id": raw_data.get("_id"),
            "title": raw_data.get("assessment_name") or raw_data.get("title", ""),
            "content": self._build_assessment_content(raw_data),
            "metadata": {
                "data_type": "training_assessment",
                "training_module": raw_data.get("training_module") or raw_data.get("module"),
                "employee_name": raw_data.get("employee_name") or raw_data.get("employee"),
                "score": raw_data.get("score") or raw_data.get("assessment_score"),
                "passing_score": raw_data.get("passing_score"),
                "status": raw_data.get("status") or raw_data.get("result"),
                "date": raw_data.get("date") or raw_data.get("assessment_date"),
                "attempts": raw_data.get("attempts") or raw_data.get("attempt_number"),
            }
        }
        
        processed["metadata"] = {k: v for k, v in processed["metadata"].items() if v is not None}
        return processed
    
    def process_training_feedback(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process training feedback data."""
        processed = {
            "id": raw_data.get("_id"),
            "title": f"Feedback: {raw_data.get('training_session', '')}",
            "content": self._build_feedback_content(raw_data),
            "metadata": {
                "data_type": "training_feedback",
                "training_session": raw_data.get("training_session") or raw_data.get("session"),
                "employee_name": raw_data.get("employee_name") or raw_data.get("employee"),
                "rating": raw_data.get("rating") or raw_data.get("overall_rating"),
                "feedback": raw_data.get("feedback") or raw_data.get("comments"),
                "suggestions": raw_data.get("suggestions") or raw_data.get("improvements"),
                "date": raw_data.get("date") or raw_data.get("feedback_date"),
            }
        }
        
        processed["metadata"] = {k: v for k, v in processed["metadata"].items() if v is not None}
        return processed
    
    def _build_module_content(self, data: Dict) -> str:
        """Build searchable content for training modules."""
        parts = []
        
        # Title
        title = data.get("title") or data.get("name") or data.get("module_name", "")
        if title:
            parts.append(f"Training Module: {title}")
        
        # Description
        desc = data.get("description") or data.get("content") or data.get("overview", "")
        if desc:
            parts.append(f"Description: {desc}")
        
        # Learning objectives
        if data.get("learning_objectives"):
            parts.append(f"Learning Objectives: {data['learning_objectives']}")
        
        # Duration
        if data.get("duration"):
            parts.append(f"Duration: {data['duration']}")
        
        # Category
        if data.get("category") or data.get("training_category"):
            category = data.get("category") or data.get("training_category")
            parts.append(f"Category: {category}")
        
        # Prerequisites
        if data.get("prerequisites"):
            parts.append(f"Prerequisites: {data['prerequisites']}")
        
        return "\n\n".join(parts)
    
    def _build_session_content(self, data: Dict) -> str:
        """Build searchable content for training sessions."""
        parts = []
        
        name = data.get("session_name") or data.get("title") or data.get("name", "")
        if name:
            parts.append(f"Training Session: {name}")
        
        if data.get("training_module"):
            parts.append(f"Module: {data['training_module']}")
        
        if data.get("instructor") or data.get("trainer"):
            instructor = data.get("instructor") or data.get("trainer")
            parts.append(f"Instructor: {instructor}")
        
        if data.get("date") or data.get("session_date"):
            date = data.get("date") or data.get("session_date")
            parts.append(f"Date: {date}")
        
        if data.get("location") or data.get("venue"):
            location = data.get("location") or data.get("venue")
            parts.append(f"Location: {location}")
        
        return "\n\n".join(parts)
    
    def _build_training_plan_content(self, data: Dict) -> str:
        """Build searchable content for training plans."""
        parts = []
        
        employee = data.get("employee_name") or data.get("employee", "")
        if employee:
            parts.append(f"Employee: {employee}")
        
        if data.get("department"):
            parts.append(f"Department: {data['department']}")
        
        if data.get("role") or data.get("position"):
            role = data.get("role") or data.get("position")
            parts.append(f"Role: {role}")
        
        if data.get("required_modules") or data.get("training_modules"):
            modules = data.get("required_modules") or data.get("training_modules")
            parts.append(f"Required Modules: {modules}")
        
        if data.get("completion_deadline") or data.get("deadline"):
            deadline = data.get("completion_deadline") or data.get("deadline")
            parts.append(f"Deadline: {deadline}")
        
        if data.get("completion_status"):
            parts.append(f"Status: {data['completion_status']}")
        
        return "\n\n".join(parts)
    
    def _build_attendance_content(self, data: Dict) -> str:
        """Build searchable content for attendance records."""
        parts = []
        
        if data.get("employee_name") or data.get("employee"):
            employee = data.get("employee_name") or data.get("employee")
            parts.append(f"Employee: {employee}")
        
        if data.get("training_session") or data.get("session"):
            session = data.get("training_session") or data.get("session")
            parts.append(f"Training Session: {session}")
        
        if data.get("attendance_status") or data.get("status"):
            status = data.get("attendance_status") or data.get("status")
            parts.append(f"Attendance: {status}")
        
        if data.get("date") or data.get("attendance_date"):
            date = data.get("date") or data.get("attendance_date")
            parts.append(f"Date: {date}")
        
        return "\n\n".join(parts)
    
    def _build_assessment_content(self, data: Dict) -> str:
        """Build searchable content for assessments."""
        parts = []
        
        if data.get("assessment_name") or data.get("title"):
            name = data.get("assessment_name") or data.get("title")
            parts.append(f"Assessment: {name}")
        
        if data.get("training_module") or data.get("module"):
            module = data.get("training_module") or data.get("module")
            parts.append(f"Module: {module}")
        
        if data.get("employee_name") or data.get("employee"):
            employee = data.get("employee_name") or data.get("employee")
            parts.append(f"Employee: {employee}")
        
        if data.get("score") or data.get("assessment_score"):
            score = data.get("score") or data.get("assessment_score")
            parts.append(f"Score: {score}")
        
        if data.get("status") or data.get("result"):
            status = data.get("status") or data.get("result")
            parts.append(f"Result: {status}")
        
        return "\n\n".join(parts)
    
    def _build_feedback_content(self, data: Dict) -> str:
        """Build searchable content for feedback."""
        parts = []
        
        if data.get("training_session") or data.get("session"):
            session = data.get("training_session") or data.get("session")
            parts.append(f"Training Session: {session}")
        
        if data.get("employee_name") or data.get("employee"):
            employee = data.get("employee_name") or data.get("employee")
            parts.append(f"Employee: {employee}")
        
        if data.get("rating") or data.get("overall_rating"):
            rating = data.get("rating") or data.get("overall_rating")
            parts.append(f"Rating: {rating}")
        
        if data.get("feedback") or data.get("comments"):
            feedback = data.get("feedback") or data.get("comments")
            parts.append(f"Feedback: {feedback}")
        
        if data.get("suggestions") or data.get("improvements"):
            suggestions = data.get("suggestions") or data.get("improvements")
            parts.append(f"Suggestions: {suggestions}")
        
        return "\n\n".join(parts)
    
    def _build_qualification_content(self, data: Dict) -> str:
        """Build searchable content for training qualifications."""
        parts = []
        
        name = data.get("name") or data.get("qualification_name", "")
        if name:
            parts.append(f"Qualification: {name}")
        
        if data.get("description"):
            parts.append(f"Description: {data['description']}")
        
        if data.get("requirements"):
            parts.append(f"Requirements: {data['requirements']}")
        
        if data.get("valid_for") or data.get("validity_period"):
            validity = data.get("valid_for") or data.get("validity_period")
            parts.append(f"Valid for: {validity}")
        
        if data.get("category") or data.get("qualification_type"):
            category = data.get("category") or data.get("qualification_type")
            parts.append(f"Category: {category}")
        
        return "\n\n".join(parts)
    
    async def ingest_all_training_data(self):
        """Ingest all training data types."""
        for data_type in self.TRAINING_DATA_TYPES:
            logger.info(f"Starting ingestion for {data_type}")
            
            # Fetch from Bubble
            cursor = 0
            total_records = 0
            
            while True:
                records = await self.fetch_training_data_from_bubble(
                    data_type, limit=100, cursor=cursor
                )
                
                if not records:
                    break
                
                # Process based on type
                processed_records = []
                for record in records:
                    if data_type == "TrainingModule":
                        processed = self.process_training_module(record)
                    elif data_type == "trainingsession":
                        processed = self.process_training_session(record)
                    elif data_type == "trainingplan":
                        processed = self.process_training_plan(record)
                    elif data_type == "trainingqualification":
                        processed = self.process_training_qualification(record)
                    # elif data_type == "training_attendance":
                    #     processed = self.process_training_attendance(record)
                    # elif data_type == "training_assessment":
                    #     processed = self.process_training_assessment(record)
                    # elif data_type == "training_feedback":
                    #     processed = self.process_training_feedback(record)
                    else:
                        continue
                    
                    processed_records.append(processed)
                
                # Stage in Supabase
                await self.stage_api_data(
                    processed_records, 
                    source_type="bubble",
                    data_type=data_type
                )
                
                total_records += len(records)
                cursor += len(records)
                
                # Check if we've fetched all records
                if len(records) < 100:
                    break
            
            logger.info(f"Fetched {total_records} records for {data_type}")
            
            # Process staged data
            await self.process_staged_data(data_type=data_type)
            
            # Sync to vector store
            await self.sync_to_vector_store()
            
        logger.info("Training data ingestion complete!")


# Usage example
async def main():
    pipeline = TrainingDataPipeline()
    
    # Create staging tables (run once)
    pipeline.create_staging_tables()
    
    # Ingest all training data
    await pipeline.ingest_all_training_data()


if __name__ == "__main__":
    asyncio.run(main())