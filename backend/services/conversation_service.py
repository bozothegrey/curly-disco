from datetime import datetime
from config import Config
from models.conversation import ConversationModel
from services.ai_service import AIService
import logging

logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self):
        self.conversation_model = ConversationModel()
        self.ai_service = AIService()

    def detect_conversation_start(self, user_id, force_start=False):
        """Detect if this is the start of a new conversation"""
        try:
            # Start if forced by new conversation button
            if force_start:
                logger.info(f"New conversation forced for {user_id}")
                return True

            # Check if there is an active conversation
            active_conversation = self.conversation_model.conversations_col.find_one(
                {"user_id": user_id, "conversation_complete": {"$ne": True}}
            )

            # Start if no active conversation
            if active_conversation is None:
                logger.info(f"No active conversation found for {user_id} - starting new one")
                return True
            else:
                logger.info(f"Active conversation exists for {user_id} - continuing")
                return False

        except Exception as e:
            logger.error(f"Error detecting conversation start: {str(e)}")
            return True

    def detect_conversation_end(self, user_message, user_id):
        """Detect if conversation should end based on user greetings/farewells or inactivity"""
        try:
            # Check for greetings/farewell patterns
            farewell_patterns = [
                "bye", "goodbye", "see you", "thanks", "thank you",
                "i'm done", "that's all", "gotta go", "i have to go",
                "end this conversation", "let's end", "finish this chat",
                "stop talking", "i want to stop", "conversation over",
                "chat over", "done talking", "finished"
            ]
            
            user_message_lower = user_message.lower()
            user_farewell = any(pattern in user_message_lower for pattern in farewell_patterns)
            
            if user_farewell:
                logger.info(f"User farewell detected for {user_id}: '{user_message}'")
                return True

            # Check for prolonged silence (inactivity)
            last_conversation = self.conversation_model.get_last_conversation(user_id)
            if last_conversation:
                time_diff = datetime.utcnow() - last_conversation["timestamp"]
                if time_diff.total_seconds() > Config.CONVERSATION_TIMEOUT:
                    logger.info(f"Prolonged silence detected for {user_id}: {time_diff.total_seconds():.1f}s")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error detecting conversation end: {str(e)}")
            return False

    def process_chat_message(self, user_id, user_message, force_start=False):
        """Process a chat message and return response"""
        try:
            # Detect conversation start
            is_conversation_start = self.detect_conversation_start(user_id, force_start)
            
            # Detect conversation end (check before processing)
            conversation_ended = self.detect_conversation_end(user_message, user_id)
            
            # Determine timeout based on message complexity
            word_count = len(user_message.split())
            timeout = Config.TIMEOUT_PROFILE["complex"] if word_count > 8 else Config.TIMEOUT_PROFILE["simple"]
            
            # Build prompt with context
            context = self.conversation_model.get_user_context(user_id)
            messages = [
                {"role": "system", "content": Config.SYSTEM_PROMPT},
                {"role": "system", "content": f"Previous context:\n{context}"},
                {"role": "user", "content": user_message}
            ]
            
            # Get AI response
            ai_response = self.ai_service.get_chat_response(
                messages, 
                timeout=timeout
            )
            
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

    def extract_topics(self, text):
        """Simple topic extraction for conversation summaries"""
        stopwords = {"the", "and", "a", "is", "in", "it", "to", "of", "for", "on", "with", "as", "at", "by"}
        words = [w.strip(".,!?").lower() for w in text.split()]
        return [w for w in words if w not in stopwords and len(w) > 2][:3]
