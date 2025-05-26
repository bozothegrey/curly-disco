from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os
import requests
import time
import logging
from concurrent.futures import ThreadPoolExecutor

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# MongoDB Configuration
client = MongoClient(os.getenv("MONGODB_URI"))
db = client.get_database("kids_chat")
conversations_col = db["conversations"]

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=4)

# Timeout profiles (seconds)
TIMEOUT_PROFILE = {
    "simple": 15,  # Short questions
    "complex": 30, # Long/multi-part questions
    "fallback": 5  # Emergency responses
}

# System prompt template
SYSTEM_PROMPT = """You are a friendly AI tutor for children aged 6-9. 
Key requirements:
1. Use simple words and short sentences
2. Add emojis to make it fun 🎨
3. Ask one follow-up question
4. Relate to previous topics when possible"""

SUMMARY_PROMPT = """Act as a child development expert analyzing this conversation. Create a structured summary for future reference:

**Child Profile Update**
1. Observed Interests: Identify 2-3 specific interests the child demonstrated
2. Learning Patterns: Note any curiosity patterns or learning styles shown
3. Knowledge Gaps: Highlight misunderstandings to address later

**Educational Strategy**
1. Concepts Taught: List core concepts covered (max 3)
2. Teaching Methods: Detail metaphors/analogies that worked well
3. Engagement Level: Rate 1-5 how engaged the child seemed

**Development Notes**
1. Curiosity Spark: Suggest 1 related topic to explore next
2. Parental Note: Flag any concerns (social/emotional/cognitive) with constructive suggestions
3. Positive Reinforcement: Identify 1 strength to encourage

**Format Requirements**
- Use child-friendly terms avoid technical jargon
- Keep each section under 15 words
- Emphasize interests over weaknesses
- Write in third-person neutral tone

Conversation:
{conversation_text}

Effective summary:"""

@app.route("/test-db", methods=["GET"])
def test_db():
    """Database health check endpoint"""
    try:
        client.admin.command('ping')
        return jsonify({
            "status": "success",
            "database": "kids_chat",
            "conversations_count": conversations_col.count_documents({})
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/chat", methods=["POST"])
def chat():
    """Main chat endpoint with enhanced logging"""
    start_time = time.time()
    
    try:
        # Validate request
        data = request.get_json()
        if not data or "user_id" not in data or "message" not in data:
            app.logger.error("Invalid request format")
            return jsonify({"error": "Invalid request format"}), 400

        user_id = data["user_id"]
        user_message = data["message"].strip()
        
        app.logger.info(f"New message from {user_id}: {user_message}")

        # Determine timeout tier
        word_count = len(user_message.split())
        timeout = TIMEOUT_PROFILE["complex"] if word_count > 8 else TIMEOUT_PROFILE["simple"]
        
        # Build prompt with context
        context = get_context(user_id)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"Previous context:\n{context}"},
            {"role": "user", "content": user_message}
        ]

        # API call with timing
        api_start = time.time()
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
            json={"model": "deepseek-chat", "messages": messages},
            timeout=timeout
        )
        api_time = time.time() - api_start
        app.logger.info(f"API response time: {api_time:.2f}s")

        # Handle API errors
        if response.status_code != 200:
            app.logger.error(f"API error: {response.text}")
            return jsonify({"error": "AI service unavailable"}), 500

        # Extract response
        ai_response = response.json()["choices"][0]["message"]["content"]
        app.logger.info(f"AI response: {ai_response}")

        # Async save with summary logging
        executor.submit(
            save_conversation,
            user_id,
            [
                {"text": user_message, "sender": "child"},
                {"text": ai_response, "sender": "AI"}
            ]
        )

        return jsonify({"response": ai_response})

    except requests.exceptions.Timeout:
        app.logger.warning("Request timeout")
        return jsonify({
            "response": "Hmm, this is taking longer than usual! ⏳ Why don't we talk about your favorite animal instead? 🐾"
        }), 504
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"response": "Oops! Let's try that again."}), 500

def save_conversation(user_id, messages):
    """Save conversation with detailed logging"""
    try:
        # Generate and log summary
        summary = generate_summary(messages)
        app.logger.info(f"Generated summary: {summary}")
        
        conversation = {
            "user_id": user_id,
            "timestamp": datetime.utcnow(),
            "messages": messages,
            "summary": summary,
            "topics": extract_topics(summary)
        }
        
        # Insert with timeout
        conversations_col.insert_one(conversation)
        app.logger.info(f"Saved conversation for {user_id}")

    except Exception as e:
        app.logger.error(f"Save failed: {str(e)}")

def generate_summary(messages):
    conversation_text = "\n".join([f"{m['sender']}: {m['text']}" for m in messages])
    
    prompt = f"""You are an AI teaching assistant specializing in child development. 
    {SUMMARY_PROMPT}"""
    
    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": "deepseek-chat",
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            "temperature": 0.3  # Keep outputs consistent
        }
    )
    
    return response.json()["choices"][0]["message"]["content"]

def extract_topics(text):
    """Simplified topic extraction"""
    try:
        stopwords = {"the", "and", "a", "is", "in", "it"}
        return [
            word.lower() for word in text.split() 
            if word.lower() not in stopwords
        ][:3]  # Return top 3 keywords
    except:
        return []

def get_context(user_id):
    """Get context with caching"""
    try:
        last_convos = conversations_col.find(
            {"user_id": user_id},
            sort=[("timestamp", -1)],
            limit=3
        ).limit(3)
        return "\n".join([doc["summary"] for doc in last_convos])
    except:
        return ""

@app.route("/conversations/<user_id>", methods=["GET"])
def get_conversations(user_id):
    """Get stored conversations for testing"""
    try:
        convos = list(conversations_col.find(
            {"user_id": user_id},
            {"_id": 0, "messages": 0}  # Exclude messages and IDs
        ).sort("timestamp", -1))
        return jsonify(convos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
