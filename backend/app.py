from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os
import requests

# MongoDB Atlas Connection
client = MongoClient(os.getenv("MONGODB_URI"))
db = client.get_database("kids_chat")
users_col = db["users"]
conversations_col = db["conversations"]

app = Flask(__name__)
CORS(app)

# Store conversation with AI-generated summary
def save_conversation(user_id, messages):
    summary = generate_summary(messages)  # Uses DeepSeek (see below)
    
    conversation = {
        "user_id": user_id,
        "timestamp": datetime.utcnow(),
        "messages": messages,
        "summary": summary,
        "topics": extract_topics(summary)  # Array of keywords
    }
    conversations_col.insert_one(conversation)

# Generate dynamic prompt using last 3 summaries
def get_context(user_id):
    last_convos = conversations_col.find(
        {"user_id": user_id},
        sort=[("timestamp", -1)],
        limit=3
    )
    return "\n".join([doc["summary"] for doc in last_convos])

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_id = data["user_id"]
    user_message = data["message"]
    
    # Build dynamic prompt
    context = get_context(user_id)
    prompt = f"""
    [System Note: Previous interactions:
    {context}
    
    Respond like you're talking to a curious child.
    ]
    User: {user_message}
    """
    
    # Call DeepSeek API
    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    
    # Save conversation
    save_conversation(user_id, [
        {"text": user_message, "sender": "child"},
        {"text": response.json()["choices"][0]["message"]["content"], "sender": "AI"}
    ])
    
    return jsonify({"response": response.json()})

# Helper: Generate summary using DeepSeek
def generate_summary(messages):
    conversation_text = "\n".join([f"{m['sender']}: {m['text']}" for m in messages])
    prompt = f"Summarize this child-AI chat in 1 sentence focusing on learning topics:\n\n{conversation_text}"
    
    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
        json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]}
    )
    return response.json()["choices"][0]["message"]["content"]

# Helper: Extract keywords (simplified)
def extract_topics(text):
    # For production, use DeepSeek/NLP libraries
    return list(set(text.lower().split()[:5]))  # First 5 words as mock topics

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
