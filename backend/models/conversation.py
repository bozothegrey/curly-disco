from pymongo import MongoClient
from datetime import datetime
from config import Config
import logging

logger = logging.getLogger(__name__)

class ConversationModel:
    def __init__(self):
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client.get_database(Config.DATABASE_NAME)
        self.conversations_col = self.db["conversations"]
    
    def save_conversation(self, user_id, messages, summary, topics, 
                         is_start=False, is_end=False):
        """Save a conversation to the database"""
        try:
            conversation = {
                "user_id": user_id,
                "timestamp": datetime.utcnow(),
                "messages": messages,
                "summary": summary,
                "topics": topics,
                "conversation_start": is_start,
                "conversation_end": is_end,
                "ended_at": datetime.utcnow() if is_end else None,
                "conversation_complete": is_end,
                "last_activity": datetime.utcnow()
            }
            
            result = self.conversations_col.insert_one(conversation)
            logger.info(f"Saved conversation for {user_id} (Start: {is_start}, End: {is_end})")
            return result.inserted_id
            
        except Exception as e:
            logger.error(f"Failed to save conversation: {str(e)}")
            raise
    
    def get_user_context(self, user_id, limit=3):
        """Get recent conversation context for a user"""
        try:
            conversations = self.conversations_col.find(
                {"user_id": user_id},
                {"summary": 1, "_id": 0},
                sort=[("timestamp", -1)],
                limit=limit
            )
            return "\n".join([doc.get("summary", "") for doc in conversations])
        except Exception as e:
            logger.error(f"Failed to get context for {user_id}: {str(e)}")
            return ""
    
    def get_last_conversation(self, user_id):
        """Get the most recent conversation for a user"""
        try:
            return self.conversations_col.find_one(
                {"user_id": user_id},
                sort=[("timestamp", -1)]
            )
        except Exception as e:
            logger.error(f"Failed to get last conversation for {user_id}: {str(e)}")
            return None
    
    def mark_conversation_ended(self, user_id, end_reason="manual"):
        """Mark the last active conversation as ended"""
        try:
            result = self.conversations_col.update_one(
                {"user_id": user_id, "conversation_complete": {"$ne": True}},
                {
                    "$set": {
                        "ended_at": datetime.utcnow(),
                        "end_reason": end_reason,
                        "conversation_complete": True
                    }
                },
                sort=[("timestamp", -1)]
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to mark conversation ended for {user_id}: {str(e)}")
            return False
    
    def update_last_activity(self, user_id):
        """Update the last activity timestamp"""
        try:
            # Remove the sort parameter - updateOne doesn't support it
            result = self.conversations_col.update_one(
                {"user_id": user_id, "conversation_complete": {"$ne": True}},
                {"$set": {"last_activity": datetime.utcnow()}}
            )
            
            # If no active conversation found, that's okay
            if result.matched_count == 0:
                logger.info(f"No active conversation found to update for {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to update activity for {user_id}: {str(e)}")

    
    def get_conversations_by_user(self, user_id):
        """Get all conversations for a user (excluding messages)"""
        try:
            return list(self.conversations_col.find(
                {"user_id": user_id},
                {"_id": 0, "messages": 0}
            ).sort("timestamp", -1))
        except Exception as e:
            logger.error(f"Failed to get conversations for {user_id}: {str(e)}")
            return []
    
    def get_incomplete_conversations(self, user_id):
        """Get incomplete conversations for session summary"""
        try:
            return list(self.conversations_col.find(
                {"user_id": user_id, "conversation_complete": {"$ne": True}},
                sort=[("timestamp", 1)]
            ))
        except Exception as e:
            logger.error(f"Failed to get incomplete conversations for {user_id}: {str(e)}")
            return []
    
    def update_session_summary(self, user_id, session_summary, message_count):
        """Update the final conversation with session summary"""
        try:
            # Find the most recent conversation for this user first
            recent_conversation = self.conversations_col.find_one(
                {"user_id": user_id, "conversation_end": True},
                sort=[("timestamp", -1)]
            )
            
            if recent_conversation:
                # Update by _id instead of using sort in update_one
                result = self.conversations_col.update_one(
                    {"_id": recent_conversation["_id"]},
                    {
                        "$set": {
                            "session_summary": session_summary,
                            "session_message_count": message_count
                        }
                    }
                )
                logger.info(f"Updated session summary for conversation {recent_conversation['_id']}")
            else:
                logger.warning(f"No conversation with conversation_end=True found for {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to update session summary for {user_id}: {str(e)}")

    
    def health_check(self):
        """Check database connection health"""
        try:
            self.client.admin.command('ping')
            return {
                "status": "success",
                "database": Config.DATABASE_NAME,
                "conversations_count": self.conversations_col.count_documents({})
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

