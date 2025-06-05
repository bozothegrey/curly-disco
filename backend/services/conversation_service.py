from datetime import datetime
from config import Config
from models.conversation import ConversationModel
import logging

logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self):
        self.conversation_model = ConversationModel()
        self.conversation_start_times = {}  # Track start times in memory

    def detect_conversation_start(self, user_id, force_start=False):
        """Detect if this is the start of a new conversation"""
        try:
            # Start if forced by new conversation button
            if force_start:
                logger.info(f"New conversation forced for {user_id}")
                self.conversation_start_times[user_id] = datetime.utcnow()
                return True

            # Check if there is an active conversation
            active_conversation = self.conversation_model.conversations_col.find_one(
                {"user_id": user_id, "conversation_complete": {"$ne": True}}
            )

            # Start if no active conversation
            if active_conversation is None:
                logger.info(f"No active conversation found for {user_id} - starting new one")
                self.conversation_start_times[user_id] = datetime.utcnow()
                return True
            else:
                logger.info(f"Active conversation exists for {user_id} - continuing")
                return False

        except Exception as e:
            logger.error(f"Error detecting conversation start: {str(e)}")
            return True

    def detect_conversation_end(self, user_message, user_id):
        """Detect if conversation should end based on inactivity"""
        try:
            # Only check timeout if we have a start time
            if user_id in self.conversation_start_times:
                time_diff = datetime.utcnow() - self.conversation_start_times[user_id]
                if time_diff.total_seconds() > Config.CONVERSATION_TIMEOUT:
                    logger.info(f"Conversation timeout reached for {user_id}: {time_diff.total_seconds():.1f}s")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error detecting conversation end: {str(e)}")
            return False

    def process_chat_message(self, user_id, user_message, ai_response, force_start=False):
        """Process a chat message with provided AI response"""
        try:
            # Detect conversation start
            is_conversation_start = self.detect_conversation_start(user_id, force_start)
            
            # Detect conversation end (check before processing)
            conversation_ended = self.detect_conversation_end(user_message, user_id)
            
            if conversation_ended:
                logger.info(f"Conversation ended for {user_id}")
            
            # Prepare conversation data
            conversation_data = [
                {"text": user_message, "sender": "child"},
                {"text": ai_response, "sender": "AI"}
            ]
            
            return {
                "response": ai_response,
                "conversation_data": conversation_data,
                "is_start": is_conversation_start,
                "is_end": conversation_ended
            }
            
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            raise

    def is_conversation_active(self, user_id):
        """Check if user has an active conversation"""
        try:
            active_conversation = self.conversation_model.conversations_col.find_one(
                {"user_id": user_id, "conversation_complete": {"$ne": True}}
            )
            
            return active_conversation is not None
            
        except Exception as e:
            logger.error(f"Error checking conversation status: {str(e)}")
            return False
            
    def force_end_conversation(self, user_id):
        """Forcefully end any active conversation for user"""
        try:
            # Clear in-memory start time
            if user_id in self.conversation_start_times:
                del self.conversation_start_times[user_id]
                
            # Mark conversation as ended in database
            self.conversation_model.force_end_conversation(user_id)
            logger.info(f"Forcefully ended conversation for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error forcing conversation end: {str(e)}")
            return False
