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
    
    def detect_conversation_start(self, user_id, user_message):
        """Detect if this is the start of a new conversation"""
        try:
            # Check for explicit conversation starters
            greeting_patterns = [
                "hello", "hi", "hey", "good morning", "good afternoon", 
                "good evening", "start", "new chat", "begin"
            ]
            
            message_lower = user_message.lower()
            explicit_start = any(pattern in message_lower for pattern in greeting_patterns)
            
            # Check time-based start (no activity for timeout period)
            last_conversation = self.conversation_model.get_last_conversation(user_id)
            
            time_based_start = True
            if last_conversation:
                time_diff = datetime.utcnow() - last_conversation["timestamp"]
                time_based_start = time_diff.total_seconds() > Config.CONVERSATION_TIMEOUT
            
            return explicit_start or time_based_start or last_conversation is None
            
        except Exception as e:
            logger.error(f"Error detecting conversation start: {str(e)}")
            return True  # Default to new conversation on error
    
    def detect_conversation_end(self, ai_response, user_message):
        """Detect if conversation should end"""
        try:
            # Check if AI detected end
            ai_detected_end = "CHAT-ENDED" in ai_response
            
            # Check user farewell patterns
            farewell_patterns = [
                "bye", "goodbye", "see you", "thanks", "thank you", 
                "i'm done", "that's all", "gotta go", "i have to go"
            ]
            
            user_message_lower = user_message.lower()
            user_farewell = any(pattern in user_message_lower for pattern in farewell_patterns)
            
            return ai_detected_end or user_farewell
            
        except Exception as e:
            logger.error(f"Error detecting conversation end: {str(e)}")
            return False
    
    def process_chat_message(self, user_id, user_message, force_start=False):
        """Process a chat message and return response"""
        try:
            # Detect conversation boundaries
            is_conversation_start = force_start or self.detect_conversation_start(user_id, user_message)
            
            if is_conversation_start:
                logger.info(f"New conversation started for {user_id}")
            
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
                timeout=timeout, 
                include_functions=is_conversation_start
            )
            
            # Clean up CHAT-ENDED marker for display
            display_response = ai_response.replace("CHAT-ENDED", "").strip()
            
            # Detect conversation end
            conversation_ended = self.detect_conversation_end(ai_response, user_message)
            
            if conversation_ended:
                logger.info(f"Conversation ended for {user_id}")
            
            # Prepare conversation data
            conversation_data = [
                {"text": user_message, "sender": "child"},
                {"text": display_response, "sender": "AI"}
            ]
            
            return {
                "response": display_response,
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
            last_conversation = self.conversation_model.get_last_conversation(user_id)
            
            if not last_conversation:
                return False, True  # not active, new conversation
            
            # Check if conversation is still active (within timeout window)
            time_diff = datetime.utcnow() - last_conversation["timestamp"]
            is_active = time_diff.total_seconds() < Config.CONVERSATION_TIMEOUT
            
            return is_active, not is_active
            
        except Exception as e:
            logger.error(f"Error checking conversation status: {str(e)}")
            return False, True
    
    def extract_topics(self, text):
        """Extract topics from text (simplified)"""
        try:
            stopwords = {"the", "and", "a", "is", "in", "it", "to", "of", "for"}
            words = [word.lower().strip(".,!?") for word in text.split()]
            return [word for word in words if word not in stopwords and len(word) > 2][:3]
        except:
            return []
