from flask import Blueprint, request, jsonify
from services.conversation_service import ConversationService
from services.summary_service import SummaryService
from models.conversation import ConversationModel
from config import Config
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from threading import Lock
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)
executor = ThreadPoolExecutor(max_workers=Config.MAX_WORKERS)

# In-memory storage for ongoing conversations
ongoing_conversations = defaultdict(list)
conversation_lock = Lock()

def add_message_to_session(user_id, messages):
    """Add messages to ongoing conversation session"""
    with conversation_lock:
        ongoing_conversations[user_id].extend(messages)

def get_session_messages(user_id):
    """Get all messages from current session"""
    with conversation_lock:
        return ongoing_conversations.get(user_id, [])

def clear_session_messages(user_id):
    """Clear session messages when conversation ends"""
    with conversation_lock:
        if user_id in ongoing_conversations:
            del ongoing_conversations[user_id]

def is_conversation_active(user_id):
    """Check if user has an active conversation in memory or database"""
    try:
        # Check in-memory first
        with conversation_lock:
            if user_id in ongoing_conversations and ongoing_conversations[user_id]:
                return True
        
        # Check database for incomplete conversations
        conversation_model = ConversationModel()
        active_conversation = conversation_model.conversations_col.find_one(
            {"user_id": user_id, "conversation_complete": {"$ne": True}}
        )
        
        return active_conversation is not None
    except Exception as e:
        logger.error(f"Error checking conversation status for {user_id}: {str(e)}")
        return False


@chat_bp.route("/chat", methods=["POST"])
def chat():
    """Enhanced chat endpoint - save summaries only on end"""
    start_time = time.time()
    
    try:
        # Validate request FIRST
        data = request.get_json()
        if not data or "user_id" not in data or "message" not in data:
            logger.error("Invalid request format")
            return jsonify({"error": "Invalid request format"}), 400

        # DEFINE user_id BEFORE using it
        user_id = data["user_id"]
        user_message = data["message"].strip()
        force_start = data.get("force_start", False)
        
        logger.info(f"💬 New message from {user_id}: {user_message}")
        
        # Check if conversation is already active
        conversation_already_active = is_conversation_active(user_id)
        
        # Initialize services
        conversation_service = ConversationService()
        summary_service = SummaryService()
        conversation_model = ConversationModel()
        
        # Process the message
        result = conversation_service.process_chat_message(user_id, user_message, force_start)
        
        # Override start detection if conversation is already active
        if conversation_already_active and not force_start:
            result["is_start"] = False
            logger.info(f"Overriding start detection - conversation already active for {user_id}")
        
        # Add messages to ongoing session
        add_message_to_session(user_id, result["conversation_data"])
        
        # Only save to database when conversation ends
        if result["is_end"]:
            executor.submit(
                save_final_conversation,
                user_id,
                result["conversation_data"],
                result["is_start"],
                result["is_end"],
                summary_service,
                conversation_model
            )
            logger.info(f"🔚 CONVERSATION ENDED for user {user_id} - Summary will be saved to database")
            clear_session_messages(user_id)
        else:
            session_message_count = len(get_session_messages(user_id))
            logger.info(f"💬 Message exchanged for user {user_id} (conversation ongoing - {session_message_count} messages in session)")
        
        # Prepare response
        response_data = {"response": result["response"]}
        if result["is_end"]:
            response_data["conversation_ended"] = True
        if result["is_start"] and not conversation_already_active:
            response_data["conversation_started"] = True
            logger.info(f"🆕 NEW CONVERSATION STARTED for user {user_id}")
            
        return jsonify(response_data)

    except Exception as e:
        # Make sure user_id is defined before using it in error logging
        user_id_for_log = locals().get('user_id', 'unknown')
        logger.error(f"❌ Unexpected error in chat endpoint for user {user_id_for_log}: {str(e)}")
        return jsonify({"response": "Oops! Let's try that again."}), 500


def save_final_conversation(user_id, current_messages, is_start, is_end, summary_service, conversation_model):
    """Save conversation only when it ends - with full session summary"""
    try:
        # Get all messages from the current session
        session_messages = get_session_messages(user_id)
        
        if not session_messages:
            session_messages = current_messages  # Fallback to current messages
            logger.warning(f"⚠️  No session messages found for {user_id}, using current messages as fallback")
        
        # Generate comprehensive summary for the entire session
        summary = summary_service.generate_conversation_summary(session_messages)
        
        # Extract topics
        conversation_service = ConversationService()
        topics = conversation_service.extract_topics(summary)
        
        # Save complete conversation to database
        conversation_model.save_conversation(
            user_id, session_messages, summary, topics, is_start, is_end
        )
        
        # Enhanced logging for conversation end
        logger.info(f"🎯 CONVERSATION SUMMARY SAVED: User {user_id}")
        logger.info(f"📊 Session contained {len(session_messages)} messages")
        logger.info(f"🏷️  Topics identified: {', '.join(topics) if topics else 'None'}")
        logger.info(f"⏰ Conversation ended at: {datetime.utcnow().isoformat()}")
        
        # Generate final session summary asynchronously
        executor.submit(summary_service.generate_final_session_summary, user_id)
        
    except Exception as e:
        logger.error(f"❌ Failed to save final conversation for {user_id}: {str(e)}")

# Keep the old function for backward compatibility but mark it as deprecated
def save_conversation_async(user_id, messages, is_start, is_end, summary_service, conversation_model):
    """DEPRECATED: Use save_final_conversation instead"""
    logger.warning(f"⚠️  Using deprecated save_conversation_async for {user_id}")
    save_final_conversation(user_id, messages, is_start, is_end, summary_service, conversation_model)

def is_conversation_active(user_id):
    """Check if user has an active conversation in memory or database"""
    # Check in-memory first
    with conversation_lock:
        if user_id in ongoing_conversations and ongoing_conversations[user_id]:
            return True
    
    # Check database for incomplete conversations
    conversation_model = ConversationModel()
    active_conversation = conversation_model.conversations_col.find_one(
        {"user_id": user_id, "conversation_complete": {"$ne": True}}
    )
    
    return active_conversation is not None

