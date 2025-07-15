"""
Specialized Training Data Loader for Bubble.io Integration

This module focuses on extracting, validating, and enriching training data
from Bubble.io for optimal vector search and retrieval.
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from langchain_core.documents import Document
from backend.bubble_loader import BubbleConfig, BubbleDataLoader, BubbleSyncManager

logger = logging.getLogger(__name__)


class TrainingContentParser:
    """Parse and extract structured content from training records"""
    
    @staticmethod
    def parse_editorjs_content(content_data: Any) -> List[str]:
        """Parse EditorJS JSON content into readable text"""
        text_parts = []
        
        try:
            # Ensure we have a dict
            if isinstance(content_data, str):
                content_data = json.loads(content_data)
            
            if not isinstance(content_data, dict) or "blocks" not in content_data:
                return []
            
            for block in content_data.get("blocks", []):
                block_type = block.get("type", "")
                block_data = block.get("data", {})
                
                if block_type == "paragraph":
                    text = block_data.get("text", "").strip()
                    if text:
                        # Clean HTML tags
                        text = re.sub(r'<[^>]+>', '', text)
                        text_parts.append(text)
                
                elif block_type == "header":
                    text = block_data.get("text", "").strip()
                    level = block_data.get("level", 2)
                    if text:
                        text = re.sub(r'<[^>]+>', '', text)
                        text_parts.append(f"{'#' * level} {text}")
                
                elif block_type == "list":
                    items = block_data.get("items", [])
                    style = block_data.get("style", "unordered")
                    for i, item in enumerate(items):
                        if isinstance(item, str) and item.strip():
                            item = re.sub(r'<[^>]+>', '', item)
                            prefix = f"{i+1}." if style == "ordered" else "-"
                            text_parts.append(f"{prefix} {item}")
                
                elif block_type == "checklist":
                    items = block_data.get("items", [])
                    for item in items:
                        if isinstance(item, dict):
                            text = item.get("text", "").strip()
                            checked = item.get("checked", False)
                            if text:
                                text = re.sub(r'<[^>]+>', '', text)
                                prefix = "[x]" if checked else "[ ]"
                                text_parts.append(f"{prefix} {text}")
                
                elif block_type == "quote":
                    text = block_data.get("text", "").strip()
                    caption = block_data.get("caption", "").strip()
                    if text:
                        text = re.sub(r'<[^>]+>', '', text)
                        text_parts.append(f"> {text}")
                        if caption:
                            text_parts.append(f"> — {caption}")
                
                elif block_type == "delimiter":
                    text_parts.append("---")
                
                elif block_type == "table":
                    content = block_data.get("content", [])
                    if content:
                        # Simple table representation
                        for row in content:
                            if isinstance(row, list):
                                row_text = " | ".join(str(cell) for cell in row if cell)
                                if row_text:
                                    text_parts.append(row_text)
        
        except Exception as e:
            logger.debug(f"Error parsing EditorJS content: {e}")
        
        return text_parts


class TrainingDataEnricher:
    """Enrich training data with additional metadata and context"""
    
    @staticmethod
    def calculate_content_metrics(content: str) -> Dict[str, Any]:
        """Calculate metrics about the training content"""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        
        return {
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "estimated_reading_time_minutes": max(1, len(words) // 200),  # Assuming 200 words per minute
            "has_lists": bool(re.search(r'^[-*•]\s', content, re.MULTILINE)),
            "has_headers": bool(re.search(r'^#{1,6}\s', content, re.MULTILINE)),
            "has_checklist": "[x]" in content or "[ ]" in content,
        }
    
    @staticmethod
    def extract_key_topics(content: str) -> List[str]:
        """Extract potential key topics from content"""
        topics = []
        
        # Look for headers
        headers = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
        topics.extend(headers)
        
        # Look for bold text (might be important)
        bold_text = re.findall(r'\*\*([^*]+)\*\*', content)
        topics.extend(bold_text)
        
        # Look for quoted sections
        quotes = re.findall(r'^>\s+(.+)$', content, re.MULTILINE)
        topics.extend(quotes[:3])  # Limit to first 3 quotes
        
        # Clean and deduplicate
        topics = [t.strip() for t in topics if t.strip()]
        topics = list(dict.fromkeys(topics))  # Remove duplicates while preserving order
        
        return topics[:10]  # Return top 10 topics


class TrainingDataValidator:
    """Validate training data quality"""
    
    @staticmethod
    def validate_training_content(content: str, title: str) -> Dict[str, Any]:
        """Validate training content quality"""
        issues = []
        warnings = []
        
        # Check content length
        if len(content) < 100:
            issues.append("Content too short (less than 100 characters)")
        elif len(content) < 300:
            warnings.append("Content is relatively short")
        
        # Check title
        if not title or len(title.strip()) < 5:
            issues.append("Missing or invalid title")
        
        # Check for placeholder content
        placeholder_patterns = [
            r"lorem ipsum",
            r"test content",
            r"sample text",
            r"placeholder",
            r"to be added",
            r"tbd",
            r"coming soon"
        ]
        
        content_lower = content.lower()
        for pattern in placeholder_patterns:
            if re.search(pattern, content_lower):
                warnings.append(f"Possible placeholder content detected: '{pattern}'")
        
        # Check for actual training content indicators
        training_indicators = [
            r"training",
            r"learn",
            r"objective",
            r"goal",
            r"skill",
            r"competenc",
            r"procedure",
            r"process",
            r"step",
            r"instruction"
        ]
        
        has_training_content = any(
            re.search(indicator, content_lower) 
            for indicator in training_indicators
        )
        
        if not has_training_content:
            warnings.append("Content may not be training-related")
        
        return {
            "is_valid": len(issues) == 0,
            "quality_score": max(0, 100 - len(issues) * 30 - len(warnings) * 10),
            "issues": issues,
            "warnings": warnings
        }


class EnhancedTrainingLoader(BubbleDataLoader):
    """Enhanced loader specifically for training data"""
    
    def __init__(self, config: BubbleConfig, sync_manager: BubbleSyncManager):
        super().__init__(config, sync_manager)
        self.parser = TrainingContentParser()
        self.enricher = TrainingDataEnricher()
        self.validator = TrainingDataValidator()
    
    def load_training_data(self, validate: bool = True) -> List[Document]:
        """Load and process training data with enhanced extraction"""
        documents = []
        
        logger.info("Loading training data with enhanced processing...")
        
        # Fetch training records
        records = self._fetch_records("training", since=None)
        logger.info(f"Fetched {len(records)} training records")
        
        # Process each record
        for record in records:
            doc = self._process_training_record(record, validate)
            if doc:
                documents.append(doc)
        
        # Log summary
        logger.info(f"Successfully processed {len(documents)} training documents")
        
        if validate:
            valid_docs = [d for d in documents if d.metadata.get("quality_score", 0) >= 70]
            logger.info(f"High-quality documents: {len(valid_docs)} ({len(valid_docs)/len(documents)*100:.1f}%)")
        
        return documents
    
    def _process_training_record(self, record: Dict, validate: bool) -> Optional[Document]:
        """Process a single training record with enhanced extraction"""
        try:
            # Extract basic info
            title = record.get("title", "").strip()
            record_id = record.get("_id", "")
            
            # Parse content
            content_parts = []
            
            # Add title
            if title:
                content_parts.append(f"# {title}")
                content_parts.append("")  # Empty line
            
            # Parse structured content
            if record.get("content"):
                parsed_content = self.parser.parse_editorjs_content(record["content"])
                if parsed_content:
                    content_parts.extend(parsed_content)
                    content_parts.append("")  # Empty line
            
            # Add structured fields
            if record.get("qualifications"):
                content_parts.append("## Required Qualifications")
                if isinstance(record["qualifications"], list):
                    for qual in record["qualifications"]:
                        if qual:
                            content_parts.append(f"- {qual}")
                content_parts.append("")
            
            if record.get("responsibilities"):
                content_parts.append("## Key Responsibilities")
                if isinstance(record["responsibilities"], list):
                    for resp in record["responsibilities"]:
                        if resp:
                            content_parts.append(f"- {resp}")
                content_parts.append("")
            
            if record.get("qualifiedToTrain"):
                content_parts.append("## Qualified Trainers")
                if isinstance(record["qualifiedToTrain"], list):
                    for trainer in record["qualifiedToTrain"]:
                        if trainer:
                            content_parts.append(f"- {trainer}")
                content_parts.append("")
            
            # Combine content
            page_content = "\n".join(content_parts).strip()
            
            # Validate if requested
            validation_result = {"is_valid": True, "quality_score": 100, "issues": [], "warnings": []}
            if validate:
                validation_result = self.validator.validate_training_content(page_content, title)
                if not validation_result["is_valid"]:
                    logger.warning(f"Training record {record_id} failed validation: {validation_result['issues']}")
                    return None
            
            # Calculate metrics
            metrics = self.enricher.calculate_content_metrics(page_content)
            key_topics = self.enricher.extract_key_topics(page_content)
            
            # Create metadata
            metadata = {
                # Basic metadata
                "source": f"bubble://training/{record_id}",
                "source_type": "training",
                "source_system": "bubble.io",
                "record_id": record_id,
                "title": title,
                "url": f"{self.config.app_url.rstrip('/')}/training/{record_id}",
                
                # Timestamps
                "created_date": record.get("Created Date"),
                "modified_date": record.get("Modified Date"),
                "processing_timestamp": datetime.now(timezone.utc).isoformat(),
                
                # Training-specific metadata
                "training_order": record.get("order"),
                "is_archived": record.get("isArchive", False),
                "has_sessions": bool(record.get("trainingSessions")),
                "session_count": len(record.get("trainingSessions", [])) if isinstance(record.get("trainingSessions"), list) else 0,
                
                # Content metrics
                "word_count": metrics["word_count"],
                "estimated_reading_time_minutes": metrics["estimated_reading_time_minutes"],
                "has_lists": metrics["has_lists"],
                "has_headers": metrics["has_headers"],
                "has_checklist": metrics["has_checklist"],
                
                # Extracted topics
                "key_topics": key_topics,
                
                # Quality metrics
                "quality_score": validation_result["quality_score"],
                "quality_warnings": validation_result["warnings"],
                
                # Search optimization
                "search_keywords": self._generate_search_keywords(title, key_topics),
            }
            
            # Clean metadata
            cleaned_metadata = {
                k: v for k, v in metadata.items() 
                if v is not None and v != "" and (not isinstance(v, list) or len(v) > 0)
            }
            
            return Document(
                page_content=page_content,
                metadata=cleaned_metadata
            )
            
        except Exception as e:
            logger.error(f"Error processing training record {record.get('_id', 'unknown')}: {e}")
            return None
    
    def _generate_search_keywords(self, title: str, topics: List[str]) -> List[str]:
        """Generate search keywords for better retrieval"""
        keywords = []
        
        # Add title words
        if title:
            title_words = re.findall(r'\w+', title.lower())
            keywords.extend([w for w in title_words if len(w) > 3])
        
        # Add topic words
        for topic in topics:
            topic_words = re.findall(r'\w+', topic.lower())
            keywords.extend([w for w in topic_words if len(w) > 3])
        
        # Common training terms
        keywords.extend(["training", "learning", "module", "course", "skill"])
        
        # Deduplicate and limit
        keywords = list(dict.fromkeys(keywords))[:20]
        
        return keywords


def load_enhanced_training_data() -> List[Document]:
    """
    Load training data with enhanced processing and validation.
    
    This function can be used as a drop-in replacement for regular training data loading
    with improved content extraction and metadata.
    """
    import os
    
    try:
        # Initialize configuration
        config = BubbleConfig(
            app_url=os.environ.get("BUBBLE_APP_URL", ""),
            api_token=os.environ.get("BUBBLE_API_TOKEN", ""),
            batch_size=int(os.environ.get("BUBBLE_BATCH_SIZE", "100")),
            max_content_length=int(os.environ.get("BUBBLE_MAX_CONTENT_LENGTH", "10000"))
        )
        
        if not config.app_url or not config.api_token:
            logger.warning("Bubble.io configuration missing")
            return []
        
        # Initialize sync manager
        db_url = os.environ.get("RECORD_MANAGER_DB_URL")
        if not db_url:
            logger.error("RECORD_MANAGER_DB_URL not found")
            return []
        
        sync_manager = BubbleSyncManager(db_url)
        
        # Initialize enhanced loader
        loader = EnhancedTrainingLoader(config, sync_manager)
        
        # Test connection
        if not loader.test_connection():
            logger.error("Bubble.io API connection failed")
            return []
        
        # Load training data with validation
        documents = loader.load_training_data(validate=True)
        
        # Update sync state
        if documents:
            sync_manager.update_sync_time(
                "training",
                datetime.now(timezone.utc),
                len(documents)
            )
        
        return documents
        
    except Exception as e:
        logger.error(f"Error loading enhanced training data: {e}")
        return []


if __name__ == "__main__":
    # Test the enhanced training loader
    docs = load_enhanced_training_data()
    print(f"\nLoaded {len(docs)} training documents")
    
    if docs:
        # Show sample
        sample = docs[0]
        print("\nSample document:")
        print(f"Title: {sample.metadata.get('title')}")
        print(f"Quality Score: {sample.metadata.get('quality_score')}")
        print(f"Word Count: {sample.metadata.get('word_count')}")
        print(f"Key Topics: {sample.metadata.get('key_topics', [])}")
        print(f"\nContent Preview:")
        print(sample.page_content[:500] + "...")
        print(f"\nMetadata keys: {list(sample.metadata.keys())}")