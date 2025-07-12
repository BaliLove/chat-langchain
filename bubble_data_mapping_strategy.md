# Bubble.io Data Mapping Strategy for Vector Store Integration

## Overview
This document outlines the strategy for mapping Bubble.io data types to LangChain Document format for ingestion into the vector database. Based on the schema analysis, we'll focus on extracting rich content while preserving important metadata and relationships.

## Core Mapping Principles

### 1. Document Structure
Each Bubble.io record will be transformed into a LangChain Document with:
- **page_content**: Combined rich text content from multiple fields
- **metadata**: Structured data for filtering, context, and source tracking

### 2. Content Prioritization
- **Primary Content**: Rich text fields (descriptions, content, details)
- **Secondary Content**: Titles, names, summaries
- **Contextual Content**: Categories, tags, status information
- **Metadata Only**: IDs, dates, technical fields

## Data Type Mapping Specifications

### 🎯 **Event** (Priority 1)
**Primary Content Fields:**
- Event description/details
- Event instructions
- Event content/body
- Location details

**Document Generation:**
```python
page_content = f"""
Event: {event.name}
Description: {event.description}
Instructions: {event.instructions}
Location: {event.venue_details}
Date: {event.event_date}
"""

metadata = {
    "source": f"bubble://event/{event._id}",
    "source_type": "event",
    "title": event.name,
    "event_date": event.event_date,
    "venue": event.venue,
    "category": event.category,
    "status": event.status,
    "created_date": event.created_date,
    "modified_date": event.modified_date,
    "url": f"https://app.bali.love/event/{event._id}"
}
```

### 🛍️ **Product** (Priority 1)
**Primary Content Fields:**
- Product description
- Product specifications
- Product features
- Usage instructions

**Document Generation:**
```python
page_content = f"""
Product: {product.name}
Description: {product.description}
Specifications: {product.specifications}
Features: {product.features}
Category: {product.category}
"""

metadata = {
    "source": f"bubble://product/{product._id}",
    "source_type": "product",
    "title": product.name,
    "category": product.category,
    "price": product.price,
    "availability": product.availability,
    "vendor": product.vendor,
    "created_date": product.created_date,
    "modified_date": product.modified_date,
    "url": f"https://app.bali.love/product/{product._id}"
}
```

### 🏢 **Venue** (Priority 1)
**Primary Content Fields:**
- Venue description
- Amenities list
- Policies and rules
- Location details

**Document Generation:**
```python
page_content = f"""
Venue: {venue.name}
Description: {venue.description}
Amenities: {venue.amenities}
Policies: {venue.policies}
Location: {venue.address}
Capacity: {venue.capacity}
"""

metadata = {
    "source": f"bubble://venue/{venue._id}",
    "source_type": "venue",
    "title": venue.name,
    "location": venue.address,
    "capacity": venue.capacity,
    "venue_type": venue.type,
    "availability": venue.availability,
    "created_date": venue.created_date,
    "modified_date": venue.modified_date,
    "url": f"https://app.bali.love/venue/{venue._id}"
}
```

### 💬 **Comment** (Priority 2)
**Primary Content Fields:**
- Comment text/content
- Context (what it's commenting on)

**Document Generation:**
```python
page_content = f"""
Comment on {comment.related_type}: {comment.related_title}
User: {comment.user_name}
Comment: {comment.content}
Context: {comment.context}
"""

metadata = {
    "source": f"bubble://comment/{comment._id}",
    "source_type": "comment",
    "title": f"Comment by {comment.user_name}",
    "related_type": comment.related_type,
    "related_id": comment.related_id,
    "user": comment.user_name,
    "sentiment": comment.sentiment,  # if available
    "created_date": comment.created_date,
    "url": f"https://app.bali.love/comment/{comment._id}"
}
```

### ⭐ **EventReview** (Priority 2)
**Primary Content Fields:**
- Review text
- Rating context
- Detailed feedback

**Document Generation:**
```python
page_content = f"""
Review for Event: {review.event_name}
Rating: {review.rating}/5
Review: {review.review_text}
Highlights: {review.highlights}
Suggestions: {review.suggestions}
"""

metadata = {
    "source": f"bubble://eventreview/{review._id}",
    "source_type": "event_review",
    "title": f"Review: {review.event_name}",
    "event_id": review.event_id,
    "rating": review.rating,
    "reviewer": review.reviewer_name,
    "verified": review.verified_attendance,
    "created_date": review.created_date,
    "url": f"https://app.bali.love/review/{review._id}"
}
```

### 📅 **Booking** (Priority 3)
**Primary Content Fields:**
- Special requests
- Booking notes
- Requirements

**Document Generation:**
```python
page_content = f"""
Booking for: {booking.event_name}
Guest: {booking.guest_name}
Special Requests: {booking.special_requests}
Requirements: {booking.requirements}
Notes: {booking.notes}
"""

metadata = {
    "source": f"bubble://booking/{booking._id}",
    "source_type": "booking",
    "title": f"Booking: {booking.event_name}",
    "event_id": booking.event_id,
    "guest_id": booking.guest_id,
    "status": booking.status,
    "booking_date": booking.booking_date,
    "created_date": booking.created_date,
    "url": f"https://app.bali.love/booking/{booking._id}"
}
```

## Advanced Mapping Features

### 1. Relationship Linking
Create cross-references between related entities:

```python
# For Events, include related venue and product information
if event.venue_id:
    venue_info = get_venue_summary(event.venue_id)
    page_content += f"\nVenue Details: {venue_info}"
    metadata["venue_id"] = event.venue_id

# For Bookings, include event context
if booking.event_id:
    event_info = get_event_summary(booking.event_id)
    page_content += f"\nEvent Context: {event_info}"
    metadata["event_context"] = event_info
```

### 2. Content Enrichment
Enhance documents with computed information:

```python
# Add computed fields
metadata["content_length"] = len(page_content)
metadata["content_quality_score"] = calculate_content_quality(page_content)
metadata["last_activity"] = get_last_activity_date(record)
metadata["popularity_score"] = calculate_popularity(record)
```

### 3. Multi-Language Support
Handle content in multiple languages:

```python
# Detect and tag language
detected_language = detect_language(page_content)
metadata["language"] = detected_language

# Create language-specific source identifiers
metadata["source"] = f"bubble://{data_type}/{record._id}?lang={detected_language}"
```

## Content Combination Strategies

### 1. Field Prioritization
When combining multiple text fields, prioritize by content value:

```python
def combine_content_fields(record, field_priority):
    combined_content = ""
    
    for field_name in field_priority:
        if hasattr(record, field_name) and getattr(record, field_name):
            field_value = getattr(record, field_name)
            if len(field_value.strip()) > 10:  # Only include substantial content
                combined_content += f"{field_name.title()}: {field_value}\n"
    
    return combined_content.strip()
```

### 2. Content Deduplication
Avoid duplicate content across related records:

```python
def deduplicate_content(content, existing_hashes):
    content_hash = hashlib.md5(content.encode()).hexdigest()
    
    if content_hash in existing_hashes:
        return None  # Skip duplicate content
    
    existing_hashes.add(content_hash)
    return content
```

### 3. Content Quality Filtering
Only process content that meets quality thresholds:

```python
def assess_content_quality(content):
    quality_score = 0
    
    # Length check
    if len(content) > 50:
        quality_score += 1
    if len(content) > 200:
        quality_score += 1
    
    # Content richness
    if any(word in content.lower() for word in ['description', 'details', 'information']):
        quality_score += 1
    
    # Avoid system-generated content
    if not any(pattern in content.lower() for pattern in ['auto-generated', 'system message']):
        quality_score += 1
    
    return quality_score >= 2  # Require minimum quality score
```

## Update Tracking and Incremental Sync

### 1. Change Detection
Track changes using Bubble's built-in fields:

```python
def needs_update(record, last_sync_time):
    """Check if record needs to be updated in vector store"""
    return (
        record.modified_date > last_sync_time or
        record.created_date > last_sync_time
    )
```

### 2. Sync State Management
Maintain sync state for incremental updates:

```python
sync_state = {
    "last_sync_timestamp": datetime.now(),
    "data_type_cursors": {
        "event": "2024-01-01T00:00:00Z",
        "product": "2024-01-01T00:00:00Z",
        "venue": "2024-01-01T00:00:00Z"
    },
    "total_records_processed": 0,
    "errors": []
}
```

### 3. Deletion Handling
Handle deleted records in Bubble:

```python
def sync_deletions(data_type, vector_store, bubble_existing_ids):
    """Remove documents from vector store that no longer exist in Bubble"""
    
    # Get all vector store document IDs for this data type
    vector_docs = vector_store.get_by_source_prefix(f"bubble://{data_type}/")
    vector_ids = {doc.metadata["source"].split("/")[-1] for doc in vector_docs}
    
    # Find deleted records
    deleted_ids = vector_ids - set(bubble_existing_ids)
    
    # Remove from vector store
    for deleted_id in deleted_ids:
        vector_store.delete_by_source(f"bubble://{data_type}/{deleted_id}")
```

## Error Handling and Quality Assurance

### 1. Data Validation
Validate data before processing:

```python
def validate_record(record, required_fields):
    """Validate that record has required fields for processing"""
    for field in required_fields:
        if not hasattr(record, field) or not getattr(record, field):
            return False, f"Missing required field: {field}"
    
    return True, "Valid"
```

### 2. Content Sanitization
Clean and sanitize content:

```python
def sanitize_content(content):
    """Clean and sanitize content for vector storage"""
    # Remove excessive whitespace
    content = re.sub(r'\s+', ' ', content)
    
    # Remove HTML tags if present
    content = re.sub(r'<[^>]+>', '', content)
    
    # Remove special characters that might cause issues
    content = re.sub(r'[^\w\s.,!?-]', '', content)
    
    return content.strip()
```

### 3. Monitoring and Metrics
Track integration health:

```python
integration_metrics = {
    "records_processed": 0,
    "records_skipped": 0,
    "processing_errors": 0,
    "avg_content_length": 0,
    "data_type_counts": {},
    "last_successful_sync": None
}
```

## Implementation Checklist

- [ ] Create BubbleDataMapper class
- [ ] Implement field mapping for each priority data type
- [ ] Add relationship linking logic
- [ ] Implement content quality assessment
- [ ] Create update tracking mechanism
- [ ] Add error handling and validation
- [ ] Implement incremental sync logic
- [ ] Add monitoring and metrics
- [ ] Create unit tests for mapping logic
- [ ] Document field mapping decisions

This mapping strategy provides a comprehensive foundation for transforming your Bubble.io data into a searchable vector database while maintaining data quality and relationships. 