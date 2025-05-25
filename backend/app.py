from flask import Flask, request, jsonify
import os
import requests
from flask_cors import CORS  

app = Flask(__name__)
CORS(app)  # Allow all origins (adjust in production)

# DeepSeek API Config (store these in Render's environment variables)
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # Verify this endpoint
API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# Default Kid-Friendly Prompt (centralized in backend)
DEFAULT_SYSTEM_PROMPT = """
[System Note: You're talking to a 7-year-old child. Follow these rules:
1. Use simple words and short sentences.
2. Be friendly, encouraging, and playful.
3. Avoid scary, violent, or complex topics.
4. If asked inappropriate questions, respond: "Let's talk about something fun instead!"
]
"""

@app.route("/deepseek-proxy", methods=["POST"])
def handle_query():
    # Validate JSON
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Request must be JSON"}), 415
    except:
        return jsonify({"error": "Invalid JSON"}), 400

    # Extract user input and prepend kid-friendly instructions
    user_message = data.get("prompt", "")
    full_prompt = f"{DEFAULT_SYSTEM_PROMPT}\n\nUser: {user_message}"

    # Call DeepSeek API
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},  # System message
            {"role": "user", "content": user_message}               # User input
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise HTTP errors
        ai_response = response.json()["choices"][0]["message"]["content"]
        return jsonify({"response": ai_response})
    
    except requests.exceptions.RequestException as e:
        return jsonify({"response": "Sorry, I couldn't connect. Try again later!"}), 500
    except KeyError:
        return jsonify({"response": "Received unexpected API response."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
