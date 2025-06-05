from flask import Blueprint, jsonify
from models.conversation import ConversationModel
import logging

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)

@health_bp.route("/test-db", methods=["GET", "OPTIONS"])
def test_db():
    """Database health check endpoint"""
    try:
        conversation_model = ConversationModel()
        health_status = conversation_model.health_check()
        
        if health_status["status"] == "success":
            return jsonify(health_status)
        else:
            return jsonify(health_status), 500
            
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@health_bp.route("/health", methods=["GET", "OPTIONS"])
def health():
    """General health check"""
    return jsonify({"status": "healthy", "service": "kids_chat_api"})
