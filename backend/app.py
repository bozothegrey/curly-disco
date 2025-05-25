from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/deepseek-proxy", methods=["POST"])
def handle_query():
    data = request.json
    child_prompt = data.get("prompt", "")
    # Add your child-prefixing logic here
    response = f"AI says: {child_prompt}"  # Replace with actual DeepSeek API call
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
