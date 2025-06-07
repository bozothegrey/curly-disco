from flask import Blueprint, request, jsonify
from models.conversation import ConversationModel
from services.ai_service import AIService
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

conversation_bp = Blueprint('conversation', __name__)
executor = ThreadPoolExecutor(max_workers=2)

@conversation_bp.route("/api/end-conversation", methods=["POST"])
def end_conversation():    
        
    try:
        # Handle both JSON and FormData
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = {
                'user_id': request.form.get('user_id'),
                'action': request.form.get('action', 'page_close')
            }
        
        user_id = data.get("user_id")
        end_reason = data.get("action", "page_close")
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        # Get all messages from chat session
        from routes.chat_routes import get_session_messages
        messages = get_session_messages(user_id)
        
        if not messages:
            # Try to get messages from last incomplete conversation
            last_conv = conversation_model.get_last_conversation(user_id)
            if last_conv and not last_conv.get("conversation_complete"):
                messages = last_conv.get("messages", [])
            
            if not messages:
                logger.error(f"No messages found for user {user_id}")
                return jsonify({
                    "error": "No messages found",
                    "debug": {
                        "session_messages": bool(get_session_messages(user_id)),
                        "last_conversation": bool(last_conv)
                    }
                }), 400
            
        conversation_model = ConversationModel()
        ai_service = AIService()
        
        # Generate comprehensive summary        
        summary = ai_service.generate_summary(messages, conversation_model.get_last_summary)
        topics = ai_service.extract_topics(messages)
        
        # Save complete conversation
        conversation_model.save_conversation(
            user_id,
            messages,
            summary,
            topics,
            is_start=False,
            is_end=True
        )
        
        logger.info(f"🔚 CONVERSATION SAVED: User {user_id}")
        logger.info(f"📝 End reason: {end_reason}")
        logger.info(f"📊 Messages in conversation: {len(messages)}")

        n_msg = len(messages)       
        
        # Force clear any active conversation state
        conversation_model.mark_conversation_ended(user_id, end_reason)
        from routes.chat_routes import clear_session_messages
        clear_session_messages(user_id)

        return jsonify({
            "status": "conversation_ended",
            "message_count": n_msg
        })
        
    except Exception as e:
        logger.error(f"❌ Error ending conversation: {str(e)}")
        return jsonify({"error": "Failed to end conversation"}), 500


@conversation_bp.route("/api/auto-save", methods=["POST"])
def auto_save():
    """Periodic auto-save during conversation"""
    try:
        data = request.get_json() or {}
        user_id = data.get("user_id")
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        conversation_model = ConversationModel()
        conversation_model.update_last_activity(user_id)
        
        return jsonify({"status": "auto_saved"})
        
    except Exception as e:
        logger.error(f"Auto-save error: {str(e)}")
        return jsonify({"error": "Auto-save failed"}), 500

@conversation_bp.route("/api/conversation-status/<user_id>", methods=["GET"])
def get_conversation_status(user_id):
    """Check if user has an active conversation"""
    try:
        conversation_model = ConversationModel()
        last_conversation = conversation_model.get_last_conversation(user_id)
        
        if not last_conversation:
            return jsonify({"active": False, "new_conversation": True})
        
        # Check if conversation is complete
        is_active = not last_conversation.get("conversation_complete", False)
        is_new = False  # Assume not new if we found a conversation
        
        return jsonify({
            "active": is_active,
            "new_conversation": is_new,
            "last_activity": last_conversation["timestamp"].isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error checking conversation status: {str(e)}")
        return jsonify({"error": "Status check failed"}), 500

@conversation_bp.route("/conversations/<user_id>", methods=["GET"])
#Raw data: /conversations/2
#Summary: /conversations/2?summary=true
def get_conversations(user_id):
    """Get stored conversations for a user (raw or summary)"""
    try:
        conversation_model = ConversationModel()
        conversations = conversation_model.get_conversations_by_user(user_id)
        
        # Check for ?summary=true in the query string
        summary = request.args.get('summary', 'false').lower() == 'true'
        if summary:
            formatted = []
            for conv in conversations:
                formatted.append({
                    'timestamp': conv['timestamp'].isoformat(),
                    'summary': conv.get('summary', 'No summary'),
                    'topics': conv.get('topics', []),
                    'complete': conv.get('conversation_complete', False),
                    'message_count': len(conv.get('messages', []))
                })
            return jsonify({
                'user_id': user_id,
                'conversation_count': len(formatted),
                'conversations': formatted
            })
        else:
            return jsonify(conversations)
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        return jsonify({"error": str(e)}), 500
