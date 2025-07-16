# Bubble API Reality Check

## Actual API Structure

Based on testing the live Bubble API at `app.bali.love`, here's what actually exists:

### API Base URL
- Working format: `https://app.bali.love/api/1.1/obj/{datatype}`
- Authentication: Bearer token in Authorization header
- Response format: JSON with structure:
  ```json
  {
    "response": {
      "cursor": 0,
      "results": [...],
      "count": 1234,
      "remaining": 1233
    }
  }
  ```

### Discovered Data Types (31 total)

#### Event Management
- **Event** - Main event records (weddings, etc.)
  - Key fields: name, status, code, hosts, eventType, isWedding
  - Has references to: satellite, team, leadInformation
  
- **event** (lowercase) - Same as Event but different field structure
  - Key fields: name, status, contactName, creationDate
  
- **EventReview** - Event feedback/reviews
  - Key fields: event, reviewStatus, reviewEmailSentDate
  
- **EventRSVP** - RSVP tracking
  - Key fields: rsvpQuestion, event, flow

- **EventSatellite** - Related event data
  - Key fields: event, clientTZOffset

#### Booking System
- **Booking** / **booking** - Reservation records
  - Key fields: code, satellite, bill, clientPayments, fullyPaidVendor
  - Financial tracking: totalBuy, totalSell, currency
  
- **AutomationBookingCondition** - Booking automation rules
  - Key fields: automation, dateType

#### User/Guest Management  
- **Guest** / **guest** - Guest profiles
  - Key fields: firstName, lastName, email, phone, client
  - Relationships: guestEvents, guestLists
  
- **GuestList** - Guest list management
  - Key fields: guests, client
  
- **GuestEvent** - Guest-event associations
  - Key fields: guest, event, rsvpStatus, specialRole

#### Venues & Vendors
- **Venue** / **venue** - Venue information
  - Key fields: name, area, seats, eventTypes, isPublish
  - Different structures between uppercase/lowercase versions
  
- **VenueImage** - Venue photos
  - Key fields: ceremonyImages, generalImages, receptionImages
  
- **Vendor** - Service providers
  - Key fields: companyName, categories, eventTypes, IsPreferred
  
- **VendorImage** - Vendor portfolio images

#### Products & Services
- **Product** / **product** - Service offerings
  - Key fields: creatorName, venues, priceModel, categories
  - References: satellite, xeroID
  
- **ProductImage** - Product photos
- **ProductSatellite** - Extended product data
  - Key fields: description, currency, code, xeroID

#### Communication
- **Comment** - Comments/notes
  - Key fields: Comment Text, Parent Comment Thread
  
- **CommentThread** - Discussion threads
  - Key fields: itemType, issue, followedBy
  
- **InboxConversation** - Messaging system
  - Key fields: Assignee, Last Message, Status
  
- **InboxConversationUser** - User-specific inbox data

#### Financial
- **Payment** / **payment** - Payment records
  - Key fields: currency, paymentStatus, paymentDate, paidAmountUSD

#### Training (EXISTS!)
- **training** - Training modules
  - Key fields: title, content, trainingSessions, qualifiedToTrain
  
- **TrainingModule** - Alternative training structure
  - Similar fields to training

### Key Differences from Documentation

1. **No underscore naming**: The API uses `TrainingModule` not `training_module`
2. **Case sensitivity**: Both `Event` and `event` exist as separate types
3. **Limited records**: Most types show only 1 record (might be test data or permissions)
4. **Training exists**: But as `training` and `TrainingModule`, not the expected format

### Recommendations

1. **Use exact case**: The API is case-sensitive
2. **Test both versions**: Try both uppercase and lowercase variants
3. **Check permissions**: The low record counts suggest API token might have limited access
4. **Focus on these types for RAG**:
   - Event/event - Rich event descriptions
   - Venue/venue - Location details and amenities  
   - Product/product - Service descriptions
   - Vendor - Provider information
   - Comment - User-generated content

### Next Steps

1. Get full API access if current token is limited
2. Map exact field names for each data type
3. Build ingestion pipeline using correct data type names
4. Handle both uppercase and lowercase variants