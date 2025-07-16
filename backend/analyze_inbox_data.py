"""
Analyze inbox data to understand event code mapping and contact information.
This script analyzes without requiring full environment setup.
"""
import os
import logging
import asyncio
from typing import Dict, List, Any, Optional
from collections import defaultdict
import re

from dotenv import load_dotenv
from bubble_loader import BubbleConfig, BubbleDataLoader

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InboxAnalyzer:
    def __init__(self, loader):
        self.loader = loader
        self.events_cache = {}
        self.event_code_map = {}
        self.users_cache = {}
        self.event_code_patterns = []
        
    async def load_event_cache(self):
        """Load event data to analyze event code mapping"""
        logger.info("Loading event cache...")
        
        import aiohttp
        headers = {"Authorization": f"Bearer {self.loader.config.api_token}"}
        url = f"{self.loader.base_url}/event"
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {"limit": 100}
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        events = data.get("response", {}).get("results", [])
                        
                        for event in events:
                            event_id = event.get("_id")
                            event_code = event.get("code", "").strip()
                            event_name = event.get("name", "").strip()
                            
                            if event_id:
                                self.events_cache[event_id] = {
                                    "code": event_code,
                                    "name": event_name,
                                    "full_data": event
                                }
                                
                                if event_code:
                                    self.event_code_map[event_code] = event_id
                        
                        logger.info(f"Cached {len(self.events_cache)} events")
                        logger.info(f"Found {len(self.event_code_map)} events with codes")
                        
                        # Show sample event codes
                        sample_codes = list(self.event_code_map.keys())[:15]
                        logger.info(f"Sample event codes: {', '.join(sample_codes)}")
                        
                    else:
                        logger.error(f"Failed to load events: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error loading event cache: {e}")
    
    async def load_user_cache(self):
        """Load user data to analyze contact information"""
        logger.info("Loading user cache...")
        
        import aiohttp
        headers = {"Authorization": f"Bearer {self.loader.config.api_token}"}
        url = f"{self.loader.base_url}/user"
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {"limit": 100}
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        users = data.get("response", {}).get("results", [])
                        
                        for user in users:
                            user_id = user.get("_id")
                            if user_id:
                                self.users_cache[user_id] = {
                                    "name": user.get("Name", "").strip(),
                                    "email": user.get("email", "").strip(),
                                    "full_data": user
                                }
                        
                        logger.info(f"Cached {len(self.users_cache)} users")
                        
                        # Show sample users
                        sample_users = []
                        for user_id, user_info in list(self.users_cache.items())[:5]:
                            name = user_info.get("name", "No name")
                            email = user_info.get("email", "No email")
                            user_type = "internal" if "@bali.love" in email else "external"
                            sample_users.append(f"{name} ({email}) - {user_type}")
                        
                        logger.info("Sample users:")
                        for user in sample_users:
                            logger.info(f"  {user}")
                        
                    else:
                        logger.error(f"Failed to load users: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error loading user cache: {e}")
    
    def build_event_code_patterns(self):
        """Build patterns for extracting event codes from text"""
        self.event_code_patterns = [
            r'([A-Z]{2}\d{6}(?:BBG|VV|GN))',
            r'([A-Z]{2,4}LEAD)',
            r'([A-Z]{2,4}\d{6}[A-Z]{2,3})',
        ]
        logger.info(f"Built {len(self.event_code_patterns)} event code patterns")
    
    def extract_event_code_from_text(self, text: str) -> Optional[str]:
        """Extract event code from text"""
        if not text:
            return None
            
        for pattern in self.event_code_patterns:
            match = re.search(pattern, text.upper())
            if match:
                extracted_code = match.group(1)
                if extracted_code in self.event_code_map:
                    return extracted_code
        return None
    
    async def analyze_inbox_conversations(self):
        """Analyze inbox conversations"""
        logger.info("Analyzing inbox conversations...")
        
        import aiohttp
        headers = {"Authorization": f"Bearer {self.loader.config.api_token}"}
        url = f"{self.loader.base_url}/InboxConversation"
        
        analysis = {
            "total_conversations": 0,
            "with_direct_event_reference": 0,
            "with_extracted_event_code": 0,
            "without_event_code": 0,
            "status_distribution": defaultdict(int),
            "event_code_distribution": defaultdict(int),
            "needs_reply_count": 0,
            "sample_conversations": []
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {"limit": 100}
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        conversations = data.get("response", {}).get("results", [])
                        
                        for conv in conversations:
                            analysis["total_conversations"] += 1
                            
                            # Check direct event reference
                            event_id = conv.get("event", "")
                            event_code = None
                            
                            if event_id and event_id in self.events_cache:
                                event_code = self.events_cache[event_id].get("code")
                                if event_code:
                                    analysis["with_direct_event_reference"] += 1
                            
                            # Try to extract from subject/message
                            if not event_code:
                                subject = conv.get("Subject", "")
                                last_message = conv.get("Last Message", "")
                                
                                event_code = self.extract_event_code_from_text(subject) or self.extract_event_code_from_text(last_message)
                                
                                if event_code:
                                    analysis["with_extracted_event_code"] += 1
                            
                            # Final classification
                            if event_code:
                                analysis["event_code_distribution"][event_code] += 1
                            else:
                                analysis["without_event_code"] += 1
                                event_code = "GENERAL"
                            
                            # Status analysis
                            status = conv.get("Status", "Unknown")
                            analysis["status_distribution"][status] += 1
                            
                            # Reply analysis
                            needs_reply = status.lower() in ["open", "pending", "waiting for client", "in progress"]
                            if needs_reply:
                                analysis["needs_reply_count"] += 1
                            
                            # Sample data
                            if len(analysis["sample_conversations"]) < 10:
                                analysis["sample_conversations"].append({
                                    "subject": conv.get("Subject", "No subject"),
                                    "status": status,
                                    "event_code": event_code,
                                    "needs_reply": needs_reply,
                                    "assignee": conv.get("Assignee", ""),
                                    "has_event_reference": bool(event_id)
                                })
                        
                        logger.info(f"Analyzed {len(conversations)} conversations")
                        
                    else:
                        logger.error(f"Failed to load conversations: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error analyzing conversations: {e}")
        
        return analysis
    
    async def analyze_inbox_users(self):
        """Analyze inbox user records"""
        logger.info("Analyzing inbox user records...")
        
        import aiohttp
        headers = {"Authorization": f"Bearer {self.loader.config.api_token}"}
        url = f"{self.loader.base_url}/InboxConversationUser"
        
        analysis = {
            "total_user_records": 0,
            "users_with_emails": 0,
            "no_reply_needed_count": 0,
            "user_type_distribution": defaultdict(int),
            "sample_users": []
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {"limit": 100}
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        user_records = data.get("response", {}).get("results", [])
                        
                        for user_record in user_records:
                            analysis["total_user_records"] += 1
                            
                            # User information
                            user_id = user_record.get("User(o)", "")
                            user_info = self.users_cache.get(user_id, {})
                            
                            user_name = user_info.get("name", "")
                            user_email = user_info.get("email", "")
                            
                            if user_email:
                                analysis["users_with_emails"] += 1
                                user_type = "internal" if "@bali.love" in user_email else "external"
                                analysis["user_type_distribution"][user_type] += 1
                            
                            # Reply analysis
                            no_reply_needed = user_record.get("noReplyNeeded?", False)
                            if no_reply_needed:
                                analysis["no_reply_needed_count"] += 1
                            
                            # Sample data
                            if len(analysis["sample_users"]) < 10:
                                analysis["sample_users"].append({
                                    "name": user_name,
                                    "email": user_email,
                                    "user_type": "internal" if "@bali.love" in user_email else "external",
                                    "no_reply_needed": no_reply_needed,
                                    "destination": user_record.get("Destination", "")
                                })
                        
                        logger.info(f"Analyzed {len(user_records)} user records")
                        
                    else:
                        logger.error(f"Failed to load user records: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error analyzing user records: {e}")
        
        return analysis


async def main():
    """Main analysis function"""
    logger.info("Starting INBOX DATA ANALYSIS...")
    logger.info("This will analyze event mapping and contact information")
    
    # Initialize basic config
    config = BubbleConfig(
        app_url=os.environ.get("BUBBLE_APP_URL", ""),
        api_token=os.environ.get("BUBBLE_API_TOKEN", ""),
        batch_size=100,
        max_content_length=10000
    )
    
    # Simple loader without sync manager - create a dummy one
    from bubble_loader import BubbleSyncManager
    
    # Create a minimal sync manager for testing
    try:
        sync_manager = BubbleSyncManager("sqlite:///temp_analysis.db")
    except:
        sync_manager = None
    
    loader = BubbleDataLoader(config, sync_manager)
    
    if not loader.test_connection():
        logger.error("Bubble.io API connection failed")
        return
    
    # Initialize analyzer
    analyzer = InboxAnalyzer(loader)
    
    # Load caches
    await analyzer.load_event_cache()
    await analyzer.load_user_cache()
    analyzer.build_event_code_patterns()
    
    # Analyze data
    conversation_analysis = await analyzer.analyze_inbox_conversations()
    user_analysis = await analyzer.analyze_inbox_users()
    
    # Report results
    logger.info("=" * 60)
    logger.info("INBOX DATA ANALYSIS REPORT")
    logger.info("=" * 60)
    
    # Conversation analysis
    logger.info("\nCONVERSATION ANALYSIS:")
    logger.info(f"Total conversations: {conversation_analysis['total_conversations']}")
    logger.info(f"With direct event reference: {conversation_analysis['with_direct_event_reference']}")
    logger.info(f"With extracted event code: {conversation_analysis['with_extracted_event_code']}")
    logger.info(f"Without event code: {conversation_analysis['without_event_code']}")
    logger.info(f"Messages needing reply: {conversation_analysis['needs_reply_count']}")
    
    # Status distribution
    logger.info("\nStatus distribution:")
    for status, count in conversation_analysis['status_distribution'].items():
        logger.info(f"  {status}: {count}")
    
    # Event code distribution
    logger.info("\nEvent code distribution:")
    for event_code, count in sorted(conversation_analysis['event_code_distribution'].items(), key=lambda x: x[1], reverse=True)[:10]:
        logger.info(f"  {event_code}: {count}")
    
    # User analysis
    logger.info("\nUSER ANALYSIS:")
    logger.info(f"Total user records: {user_analysis['total_user_records']}")
    logger.info(f"Users with emails: {user_analysis['users_with_emails']}")
    logger.info(f"No reply needed: {user_analysis['no_reply_needed_count']}")
    
    # User type distribution
    logger.info("\nUser type distribution:")
    for user_type, count in user_analysis['user_type_distribution'].items():
        logger.info(f"  {user_type}: {count}")
    
    # Sample conversations
    logger.info("\nSAMPLE CONVERSATIONS:")
    for i, conv in enumerate(conversation_analysis['sample_conversations'][:5]):
        logger.info(f"  {i+1}. Event: {conv['event_code']} | Subject: {conv['subject'][:50]}...")
        logger.info(f"      Status: {conv['status']} | Needs reply: {conv['needs_reply']}")
    
    # Sample users
    logger.info("\nSAMPLE USERS:")
    for i, user in enumerate(user_analysis['sample_users'][:5]):
        logger.info(f"  {i+1}. {user['name']} ({user['email']}) - {user['user_type']}")
    
    # Wedding-specific search capability
    logger.info("\n" + "=" * 60)
    logger.info("WEDDING-SPECIFIC SEARCH CAPABILITY ANALYSIS")
    logger.info("=" * 60)
    
    # Calculate coverage
    total_conversations = conversation_analysis['total_conversations']
    with_event_codes = conversation_analysis['with_direct_event_reference'] + conversation_analysis['with_extracted_event_code']
    coverage_percentage = (with_event_codes / total_conversations) * 100 if total_conversations > 0 else 0
    
    logger.info(f"\nEvent code coverage: {coverage_percentage:.1f}%")
    logger.info(f"Contact email coverage: {(user_analysis['users_with_emails'] / user_analysis['total_user_records']) * 100:.1f}%")
    
    # Use cases
    logger.info("\nENABLED USE CASES:")
    logger.info("1. Search all messages for wedding KM150726VV")
    logger.info("2. Find unreplied messages for specific wedding")
    logger.info("3. Get contact emails for wedding participants")
    logger.info("4. Track reply status across all communications")
    
    # Recommendations
    logger.info("\nRECOMMENDATIONS:")
    if conversation_analysis['without_event_code'] > 0:
        logger.info(f"- {conversation_analysis['without_event_code']} messages need event code assignment")
    if user_analysis['total_user_records'] > user_analysis['users_with_emails']:
        missing_emails = user_analysis['total_user_records'] - user_analysis['users_with_emails']
        logger.info(f"- {missing_emails} user records missing email information")
    
    logger.info("- Enhanced ingestion script ready for production use")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())