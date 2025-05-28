from services.ai_service import AIService
from models.conversation import ConversationModel
import logging

logger = logging.getLogger(__name__)

class SummaryService:
    def __init__(self):
        self.ai_service = AIService()
        self.conversation_model = ConversationModel()
    
    def generate_conversation_summary(self, messages):
        """Generate summary for a conversation"""
        try:
            conversation_text = "\n".join([f"{m['sender']}: {m['text']}" for m in messages])
            return self.ai_service.generate_summary(conversation_text)
        except Exception as e:
            logger.error(f"Failed to generate conversation summary: {str(e)}")
            return "Summary generation failed"
    
    def generate_final_session_summary(self, user_id):
        """Generate comprehensive summary when conversation session ends"""
        try:
            # Get all incomplete conversations for this session
            incomplete_conversations = self.conversation_model.get_incomplete_conversations(user_id)
            
            if not incomplete_conversations:
                logger.info(f"No incomplete conversations found for {user_id}")
                return
            
            # Combine all messages from the session
            all_messages = []
            for conv in incomplete_conversations:
                all_messages.extend(conv.get("messages", []))
            
            if not all_messages:
                logger.info(f"No messages found in session for {user_id}")
                return
            
            # Generate comprehensive session summary
            conversation_text = "\n".join([f"{m['sender']}: {m['text']}" for m in all_messages])
            session_summary = self.ai_service.generate_session_summary(conversation_text)
            
            # Update the database with session summary
            self.conversation_model.update_session_summary(
                user_id, 
                session_summary, 
                len(all_messages)
            )
            
            logger.info(f"Generated final session summary for {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate final session summary: {str(e)}")
