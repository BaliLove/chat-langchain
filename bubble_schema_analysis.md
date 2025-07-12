# Bubble.io Application Schema Analysis

## Overview
This document analyzes the data structure of the Bubble.io application based on the enabled Data API endpoints. The application appears to be a comprehensive event/booking management platform with extensive functionality.

## API Configuration
- **Data API Root URL**: https://app.bali.love/api/1.1/obj/
- **Total Data Types**: ~80+ enabled data types
- **API Authentication**: Private key configured

## Data Type Categories

### 🎯 **Core Event Management**
- `Event` - Main event entities
- `EventReview` - Event reviews and feedback
- `EventRSVP` - Event RSVP responses
- `EventSatellite` - Satellite/related events
- `EventLoad` - Event loading/capacity data
- `RefEvent` - Event references
- `PreEvent` - Pre-event activities

### 📅 **Booking & Reservations**
- `Booking` - Main booking entities
- `BookingGuests` - Guest information for bookings
- `BookingGuestHouse` - Guest house bookings
- `AutomationBookingCondition` - Booking automation rules
- `Cabana` - Cabana/venue bookings
- `CabanaType` - Types of cabanas available

### 👤 **User & Guest Management**
- `Guest` - Guest profiles
- `GuestList` - Guest list management
- `GuestEvent` - Guest-event associations
- `GuestRedition` - Guest editing/updates
- `GuestSetting` - Guest preferences/settings
- `Teammate` - Team member profiles
- `RouteTeam` - Team routing/assignments

### 💬 **Communication & Messaging**
- `Comment` - Comments system
- `CommentReaction` - Comment reactions/likes
- `CommentExtended` - Extended comment data
- `CommentThread` - Comment threading
- `Inbox Conversation` - Inbox conversations
- `Inbox Conversation User` - User-specific inbox data
- `InboxPFMessaggi` - Platform messages
- `AutomationMessagequeue` - Automated messaging queue

### 💰 **Payments & Transactions**
- `Payment` - Payment records
- `Payroll` - Payroll management
- `TransactionDelay` - Transaction delays
- `TransactionTask` - Transaction tasks
- `ProductLinks` - Product linking
- `ProductImage` - Product images
- `ProductConference` - Product conferences
- `ProductSatellite` - Related products

### 🛍️ **Products & Inventory**
- `Product` - Main product catalog
- `ProductAutocompleteCategory` - Product categorization
- `ProductSatellite` - Related/satellite products
- `ProductLinks` - Product relationships
- `ProductImage` - Product imagery
- `ProductConference` - Product conferences

### 🏢 **Venue & Location Management**
- `Venue` - Venue information
- `VenueImage` - Venue images
- `VenueSchedule` - Venue scheduling
- `Vendor` - Vendor management
- `VendorImage` - Vendor images

### 🔄 **Automation & Workflows**
- `AutomationBookingCondition` - Booking automation
- `AutomationMessagequeue` - Message automation
- `AutomationTaskAction` - Task automation
- `AutomationUserCreatedCondition` - User creation automation
- `AutomationNotificationAction` - Notification automation
- `WorkflowMetrics` - Workflow performance data
- `Flow` - Workflow flows
- `FlowNotification` - Flow notifications

### 📋 **Task & Project Management**
- `TransactionTask` - Transaction-related tasks
- `AutomationTaskAction` - Automated task actions
- `TaskItemsList` - Task management
- `TemporaryAttachment` - Temporary file attachments
- `TrainingQualification` - Training/qualification tracking

### 📱 **Platform & Technical**
- `SpPlatform` - Special platform data
- `PlatformScheduleWithgrass` - Platform scheduling
- `StyleGuide` - UI/styling guidelines
- `UserAdditionalData` - Extended user data
- `WallActivity` - Activity wall/feed
- `LiveMailed` - Live mailing system

### 🔐 **Security & Access**
- `EventOTPVerification` - OTP verification for events
- `Relations` - Relationship management
- `RelationalHomeperson` - Relational data
- `Responsibility` - User responsibilities
- `ResponsibilityCategory` - Responsibility categorization

### 📊 **Analytics & Monitoring**
- `WorkflowMetrics` - Workflow performance
- `HealthScore` - System health metrics
- `InboxMessages` - Message analytics
- `TransferEngineering` - Transfer tracking

## High-Value Content for Vector Search

### 🎯 **Primary Targets** (Rich Text Content)
1. **Event** - Event descriptions, details, instructions
2. **Product** - Product descriptions, specifications
3. **Venue** - Venue descriptions, amenities, policies
4. **Comment** - User-generated content, reviews, discussions
5. **EventReview** - Detailed event feedback and reviews

### 🎯 **Secondary Targets** (Metadata-Rich)
1. **Booking** - Booking details, special requests
2. **Guest** - Guest profiles, preferences, notes
3. **Vendor** - Vendor descriptions, services, capabilities
4. **Flow** - Process documentation, instructions

### 🎯 **Supporting Data** (Contextual)
1. **GuestList** - Context for events and relationships
2. **Relations** - Relationship context
3. **UserAdditionalData** - Extended user context

## Recommended Integration Strategy

### Phase 1: Core Content Types
Start with the highest-value content types that likely contain rich, searchable text:
- Event (descriptions, instructions, details)
- Product (descriptions, specifications)
- Venue (descriptions, policies, amenities)
- Comment (user discussions, feedback)
- EventReview (detailed reviews)

### Phase 2: Contextual Data
Add supporting data that provides context:
- Booking (for event context)
- Guest (for personalization)
- Vendor (for service context)

### Phase 3: Advanced Features
- Real-time updates via webhooks
- Relationship mapping between entities
- Advanced filtering and search

## Technical Considerations

### Content Processing Strategy
1. **Rich Text Fields**: Event descriptions, product details, venue information
2. **Metadata Extraction**: Dates, locations, categories, tags
3. **Relationship Mapping**: Link related entities (Event→Venue→Guest)
4. **Content Deduplication**: Handle similar content across related entities

### Update Frequency
- **High Frequency**: Comments, Messages, Bookings
- **Medium Frequency**: Events, Products, Venues
- **Low Frequency**: Users, Settings, Configuration

## Next Steps
1. Connect to API and sample actual data
2. Analyze content quality and structure
3. Design metadata schema mapping
4. Implement incremental update strategy
5. Create monitoring and quality controls 