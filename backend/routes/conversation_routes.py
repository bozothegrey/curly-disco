from flask import Blueprint, request, jsonify
from models.conversation import ConversationModel
from services.summary_service import SummaryService
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

conversation_bp = Blueprint('conversation', __name__)
executor = ThreadPoolExecutor(max_workers=2)

@conversation_bp.route("/api/end-conversation", methods=["POST"])
def end_conversation():
    """Handle forced conversation end with enhanced logging"""
    try:
        # Handle both JSON and FormData
        if request.is_json:
            data = request.get_json() or {}
        else:
            # Handle FormData from sendBeacon
            data = {
                'user_id': request.form.get('user_id'),
                'action': request.form.get('action', 'page_close')
            }
        
        user_id = data.get("user_id")
        end_reason = data.get("action", "page_close")
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        conversation_model = ConversationModel()
        success = conversation_model.mark_conversation_ended(user_id, end_reason)
        
        if success:
            logger.info(f"🔚 FORCED CONVERSATION END: User {user_id}")
            logger.info(f"📝 End reason: {end_reason}")
            
            # Clear session messages
            from routes.chat_routes import clear_session_messages
            clear_session_messages(user_id)
            
            # Generate final summary asynchronously
            summary_service = SummaryService()
            executor.submit(summary_service.generate_final_session_summary, user_id)
        
        return jsonify({"status": "conversation_ended"})
        
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
        
        from services.conversation_service import ConversationService
        conversation_service = ConversationService()
        is_active, is_new = conversation_service.is_conversation_active(user_id)
        
        return jsonify({
            "active": is_active,
            "new_conversation": is_new,
            "last_activity": last_conversation["timestamp"].isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error checking conversation status: {str(e)}")
        return jsonify({"error": "Status check failed"}), 500

@conversation_bp.route("/conversations/<user_id>", methods=["GET"])
def get_conversations(user_id):
    """Get stored conversations for a user"""
    try:
        conversation_model = ConversationModel()
        conversations = conversation_model.get_conversations_by_user(user_id)
        return jsonify(conversations)
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        return jsonify({"error": str(e)}), 500
