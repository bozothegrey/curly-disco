from flask import Blueprint, request, jsonify
from services.conversation_service import ConversationService
from services.summary_service import SummaryService
from models.conversation import ConversationModel
from config import Config
from concurrent.futures import ThreadPoolExecutor
import time
import logging

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)
executor = ThreadPoolExecutor(max_workers=Config.MAX_WORKERS)

@chat_bp.route("/chat", methods=["POST"])
def chat():
    """Enhanced chat endpoint with conversation boundary detection"""
    start_time = time.time()
    
    try:
        # Validate request
        data = request.get_json()
        if not data or "user_id" not in data or "message" not in data:
            logger.error("Invalid request format")
            return jsonify({"error": "Invalid request format"}), 400

        user_id = data["user_id"]
        user_message = data["message"].strip()
        force_start = data.get("force_start", False)
        
        logger.info(f"New message from {user_id}: {user_message}")
        
        # Initialize services
        conversation_service = ConversationService()
        summary_service = SummaryService()
        conversation_model = ConversationModel()
        
        # Process the message
        result = conversation_service.process_chat_message(user_id, user_message, force_start)
        
        # Save conversation asynchronously
        executor.submit(
            save_conversation_async,
            user_id,
            result["conversation_data"],
            result["is_start"],
            result["is_end"],
            summary_service,
            conversation_model
        )
        
        # Prepare response
        response_data = {"response": result["response"]}
        if result["is_end"]:
            response_data["conversation_ended"] = True
        if result["is_start"]:
            response_data["conversation_started"] = True
            
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        return jsonify({"response": "Oops! Let's try that again."}), 500

def save_conversation_async(user_id, messages, is_start, is_end, summary_service, conversation_model):
    """Async function to save conversation with summary"""
    try:
        # Generate summary
        summary = summary_service.generate_conversation_summary(messages)
        
        # Extract topics
        conversation_service = ConversationService()
        topics = conversation_service.extract_topics(summary)
        
        # Save to database
        conversation_model.save_conversation(
            user_id, messages, summary, topics, is_start, is_end
        )
        
        # If conversation ended, generate final session summary
        if is_end:
            executor.submit(summary_service.generate_final_session_summary, user_id)
            
    except Exception as e:
        logger.error(f"Failed to save conversation async: {str(e)}")
