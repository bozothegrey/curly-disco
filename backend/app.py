from flask import Flask, request, jsonify
import os
import requests  # Add this to call DeepSeek's API

app = Flask(__name__)

# Replace with your DeepSeek API key (if needed)
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # Hypothetical endpoint
API_KEY = os.environ.get("DEEPSEEK_API_KEY")  # Store in Render's environment variables

@app.route("/deepseek-proxy", methods=["POST"])
def handle_query():
    try:
    data = request.get_json(force=True)  # Force JSON parsing
    if not data:
        return jsonify({"error": "Request must be JSON"}), 415
    except:
        return jsonify({"error": "Invalid JSON"}), 400
    data = request.json
    child_prompt = data.get("prompt", "")

    # Call DeepSeek's API (adjust to match their actual API requirements)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": child_prompt}],
        "temperature": 0.7
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise errors for bad status codes
        ai_response = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No response.")
        return jsonify({"response": ai_response})

    except Exception as e:
        return jsonify({"response": f"Error calling DeepSeek: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
