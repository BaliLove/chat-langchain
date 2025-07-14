"""Direct training data ingestion to Pinecone (bypassing Supabase staging)"""

import os
import asyncio
from typing import List, Dict, Any
import hashlib
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

# Load environment
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample training data for testing
SAMPLE_TRAINING_DATA = {
    "training_modules": [
        {
            "_id": "module-001",
            "title": "Customer Service Excellence",
            "description": "Learn the fundamentals of providing exceptional customer service, including communication skills, problem-solving techniques, and handling difficult situations.",
            "category": "Customer Service",
            "duration": "2 hours",
            "prerequisites": "None",
            "learning_objectives": "Understand customer needs, Develop active listening skills, Handle complaints effectively, Build customer loyalty"
        },
        {
            "_id": "module-002", 
            "title": "Health and Safety in Hospitality",
            "description": "Essential health and safety procedures for hospitality staff, covering workplace hazards, emergency procedures, food safety, and COVID-19 protocols.",
            "category": "Compliance",
            "duration": "3 hours",
            "prerequisites": "Employee Orientation",
            "learning_objectives": "Identify workplace hazards, Follow safety procedures, Understand food safety requirements, Implement COVID protocols"
        },
        {
            "_id": "module-003",
            "title": "Upselling and Cross-selling Techniques", 
            "description": "Master the art of increasing revenue through effective upselling and cross-selling strategies while maintaining excellent customer experience.",
            "category": "Sales",
            "duration": "90 minutes",
            "prerequisites": "Customer Service Excellence",
            "learning_objectives": "Identify upselling opportunities, Present offers naturally, Handle objections, Track success metrics"
        }
    ],
    "training_sessions": [
        {
            "_id": "session-001",
            "session_name": "Customer Service Excellence - January Cohort",
            "training_module": "Customer Service Excellence",
            "instructor": "Sarah Johnson",
            "date": "2024-01-15",
            "time": "10:00 AM",
            "location": "Main Conference Room",
            "capacity": 20,
            "status": "scheduled"
        },
        {
            "_id": "session-002",
            "session_name": "Health & Safety Training - Q1",
            "training_module": "Health and Safety in Hospitality",
            "instructor": "Mike Chen",
            "date": "2024-01-22",
            "time": "2:00 PM", 
            "location": "Training Center",
            "capacity": 30,
            "status": "scheduled"
        }
    ],
    "employee_training_plans": [
        {
            "_id": "plan-001",
            "employee_name": "John Smith",
            "employee_id": "EMP001",
            "department": "Front Desk",
            "role": "Guest Services Representative",
            "required_modules": ["Customer Service Excellence", "Health and Safety in Hospitality", "Upselling and Cross-selling Techniques"],
            "completion_deadline": "2024-02-28",
            "completion_status": "in_progress",
            "manager": "Lisa Anderson"
        },
        {
            "_id": "plan-002",
            "employee_name": "Maria Garcia",
            "employee_id": "EMP002",
            "department": "Restaurant",
            "role": "Server",
            "required_modules": ["Customer Service Excellence", "Health and Safety in Hospitality", "Wine Service Basics"],
            "completion_deadline": "2024-03-15",
            "completion_status": "not_started",
            "manager": "Robert Taylor"
        }
    ]
}


class DirectTrainingIngestion:
    """Direct ingestion to Pinecone without Supabase staging"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small", 
            dimensions=1024, 
            chunk_size=200
        )
        self.vector_store = PineconeVectorStore(
            index_name=os.getenv("PINECONE_INDEX_NAME"),
            embedding=self.embeddings
        )
        
    def process_training_module(self, module: Dict[str, Any]) -> Document:
        """Convert training module to document"""
        content_parts = [
            f"Training Module: {module.get('title', '')}",
            f"Category: {module.get('category', '')}",
            f"Description: {module.get('description', '')}",
            f"Duration: {module.get('duration', '')}",
            f"Prerequisites: {module.get('prerequisites', 'None')}",
            f"Learning Objectives: {module.get('learning_objectives', '')}"
        ]
        
        content = "\n\n".join(filter(None, content_parts))
        
        metadata = {
            "source": module.get("_id", ""),
            "source_type": "training_module",
            "title": module.get("title", ""),
            "category": module.get("category", ""),
            "duration": module.get("duration", ""),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return Document(page_content=content, metadata=metadata)
    
    def process_training_session(self, session: Dict[str, Any]) -> Document:
        """Convert training session to document"""
        content_parts = [
            f"Training Session: {session.get('session_name', '')}",
            f"Module: {session.get('training_module', '')}",
            f"Instructor: {session.get('instructor', '')}",
            f"Date: {session.get('date', '')}",
            f"Time: {session.get('time', '')}",
            f"Location: {session.get('location', '')}",
            f"Capacity: {session.get('capacity', '')}",
            f"Status: {session.get('status', '')}"
        ]
        
        content = "\n\n".join(filter(None, content_parts))
        
        metadata = {
            "source": session.get("_id", ""),
            "source_type": "training_session",
            "title": session.get("session_name", ""),
            "training_module": session.get("training_module", ""),
            "instructor": session.get("instructor", ""),
            "date": session.get("date", ""),
            "location": session.get("location", ""),
            "status": session.get("status", ""),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return Document(page_content=content, metadata=metadata)
    
    def process_employee_training_plan(self, plan: Dict[str, Any]) -> Document:
        """Convert employee training plan to document"""
        content_parts = [
            f"Employee Training Plan for {plan.get('employee_name', '')}",
            f"Employee ID: {plan.get('employee_id', '')}",
            f"Department: {plan.get('department', '')}",
            f"Role: {plan.get('role', '')}",
            f"Manager: {plan.get('manager', '')}",
            f"Required Modules: {', '.join(plan.get('required_modules', []))}",
            f"Completion Deadline: {plan.get('completion_deadline', '')}",
            f"Status: {plan.get('completion_status', '')}"
        ]
        
        content = "\n\n".join(filter(None, content_parts))
        
        metadata = {
            "source": plan.get("_id", ""),
            "source_type": "employee_training_plan",
            "employee_name": plan.get("employee_name", ""),
            "department": plan.get("department", ""),
            "role": plan.get("role", ""),
            "status": plan.get("completion_status", ""),
            "deadline": plan.get("completion_deadline", ""),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return Document(page_content=content, metadata=metadata)
    
    async def ingest_sample_data(self):
        """Ingest sample training data"""
        all_documents = []
        
        # Process training modules
        logger.info("Processing training modules...")
        for module in SAMPLE_TRAINING_DATA["training_modules"]:
            doc = self.process_training_module(module)
            all_documents.append(doc)
            logger.info(f"  Processed: {module['title']}")
        
        # Process training sessions
        logger.info("\nProcessing training sessions...")
        for session in SAMPLE_TRAINING_DATA["training_sessions"]:
            doc = self.process_training_session(session)
            all_documents.append(doc)
            logger.info(f"  Processed: {session['session_name']}")
        
        # Process employee training plans
        logger.info("\nProcessing employee training plans...")
        for plan in SAMPLE_TRAINING_DATA["employee_training_plans"]:
            doc = self.process_employee_training_plan(plan)
            all_documents.append(doc)
            logger.info(f"  Processed: Plan for {plan['employee_name']}")
        
        # Add to vector store
        logger.info(f"\nAdding {len(all_documents)} documents to Pinecone...")
        
        try:
            # Add documents in batches
            batch_size = 10
            for i in range(0, len(all_documents), batch_size):
                batch = all_documents[i:i+batch_size]
                ids = self.vector_store.add_documents(batch)
                logger.info(f"  Added batch {i//batch_size + 1}: {len(ids)} documents")
            
            logger.info("\n[SUCCESS] Sample training data ingested successfully!")
            
            # Test with a sample query
            logger.info("\nTesting with sample query...")
            results = self.vector_store.similarity_search(
                "Which employees need customer service training?",
                k=3
            )
            
            if results:
                logger.info(f"Found {len(results)} relevant documents:")
                for i, doc in enumerate(results, 1):
                    logger.info(f"\n  Result {i}:")
                    logger.info(f"    Type: {doc.metadata.get('source_type', 'unknown')}")
                    logger.info(f"    Title: {doc.metadata.get('title', 'N/A')}")
                    preview = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                    logger.info(f"    Content: {preview}")
            
        except Exception as e:
            logger.error(f"Error adding documents to Pinecone: {e}")
            raise
    
    async def query_training_data(self, query: str, k: int = 5):
        """Query the training data"""
        logger.info(f"\nQuerying: {query}")
        
        results = self.vector_store.similarity_search(query, k=k)
        
        if results:
            logger.info(f"Found {len(results)} results:")
            for i, doc in enumerate(results, 1):
                logger.info(f"\nResult {i}:")
                logger.info(f"  Type: {doc.metadata.get('source_type', 'unknown')}")
                logger.info(f"  Title: {doc.metadata.get('title', doc.metadata.get('employee_name', 'N/A'))}")
                logger.info(f"  Content Preview: {doc.page_content[:200]}...")
        else:
            logger.info("No results found.")
        
        return results


async def main():
    """Main function to run direct ingestion"""
    
    # Check if we have the necessary credentials
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("PINECONE_API_KEY"):
        logger.error("Missing required environment variables!")
        logger.error("Please set OPENAI_API_KEY and PINECONE_API_KEY in your .env file")
        return
    
    ingestion = DirectTrainingIngestion()
    
    # Ingest sample data
    await ingestion.ingest_sample_data()
    
    # Run some test queries
    logger.info("\n=== Running Test Queries ===")
    
    test_queries = [
        "Show me all customer service training modules",
        "Which employees have training deadlines in February?",
        "What training is scheduled for January?",
        "Who needs health and safety training?"
    ]
    
    for query in test_queries:
        await ingestion.query_training_data(query, k=3)
        logger.info("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())