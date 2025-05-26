from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os
import requests

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# MongoDB Configuration
client = MongoClient(os.getenv("MONGODB_URI"))  # Use environment variable directly
db = client.get_database("kids_chat")

# Create collections with validation
conversations_col = db.conversations
users_col = db.users

# Create indexes (only once, consider adding to migration script)
users_col.create_index([("user_id", 1)], unique=True)

def save_conversation(user_id, messages):
    """Save conversation with AI-generated summary"""
    try:
        summary = generate_summary(messages)
        conversation = {
            "user_id": user_id,
            "timestamp": datetime.utcnow(),
            "messages": messages,
            "summary": summary,
            "topics": extract_topics(summary)
        }
        conversations_col.insert_one(conversation)
    except Exception as e:
        app.logger.error(f"Error saving conversation: {str(e)}")

def get_context(user_id):
    """Get conversation context for dynamic prompting"""
    try:
        last_convos = conversations_col.find(
            {"user_id": user_id},
            sort=[("timestamp", -1)],
            limit=3
        )
        return "\n".join([doc["summary"] for doc in last_convos])
    except Exception as e:
        app.logger.error(f"Error fetching context: {str(e)}")
        return ""

@app.route("/test-db", methods=["GET"])
def test_db():
    """Database health check endpoint"""
    try:
        client.admin.command('ping')
        return jsonify({
            "status": "success",
            "database": "kids_chat",
            "conversations_count": conversations_col.count_documents({}),
            "users_count": users_col.count_documents({})
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/chat", methods=["POST"])
def chat():
    """Main chat processing endpoint"""
    try:
        data = request.get_json()
        if not data or "user_id" not in data or "message" not in data:
            return jsonify({"error": "Invalid request format"}), 400

        user_id = data["user_id"]
        user_message = data["message"]
        
        # Build dynamic prompt
        context = get_context(user_id)
        prompt = f"""[System Note: Previous interactions:
{context}

Respond like you're talking to a curious child.
User: {user_message}"""

        # Call DeepSeek API
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=10
        )
        
        # Handle API errors
        if response.status_code != 200:
            return jsonify({
                "error": "DeepSeek API error",
                "status_code": response.status_code
            }), 500

        ai_response = response.json()["choices"][0]["message"]["content"]
        
        # Save conversation
        save_conversation(user_id, [
            {"text": user_message, "sender": "child"},
            {"text": ai_response, "sender": "AI"}
        ])
        
        return jsonify({"response": ai_response})

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout"}), 504
    except Exception as e:
        app.logger.error(f"Chat error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def generate_summary(messages):
    """Generate conversation summary using DeepSeek"""
    try:
        conversation_text = "\n".join(
            [f"{m['sender']}: {m['text']}" for m in messages]
        )
        prompt = f"""Summarize this child-AI chat in 1 sentence focusing on learning topics:
        
        {conversation_text}"""
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
            timeout=5
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        app.logger.error(f"Summary generation failed: {str(e)}")
        return "No summary available"

def extract_topics(text):
    """Extract conversation topics (simplified version)"""
    try:
        # Basic keyword extraction (replace with proper NLP in production)
        stopwords = {"the", "and", "a", "is", "in", "it"}
        words = [word.lower() for word in text.split() if word.lower() not in stopwords]
        return list(set(words[:5]))  # Return first 5 unique non-stopwords
    except Exception as e:
        app.logger.error(f"Topic extraction failed: {str(e)}")
        return []

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
