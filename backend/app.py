from flask import Flask
from flask_cors import CORS
from routes.chat_routes import chat_bp
from routes.conversation_routes import conversation_bp
from routes.health_routes import health_bp
from utils.logging_config import setup_logging
from config import Config
from dotenv import load_dotenv
import os

# Setup logging
setup_logging()

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8000", "http://127.0.0.1:8000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})


# Register blueprints
app.register_blueprint(chat_bp)
app.register_blueprint(conversation_bp)
app.register_blueprint(health_bp)

if __name__ == "__main__":
    #checking env
    load_dotenv()  # Only loads if .env file exists
    # Add this to your app.py for debugging
    print(f"MONGODB_URI: {os.getenv('MONGODB_URI')[:20]}..." if os.getenv('MONGODB_URI') else "MONGODB_URI not set")
    print(f"DEEPSEEK_API_KEY: {os.getenv('DEEPSEEK_API_KEY')[:10]}..." if os.getenv('DEEPSEEK_API_KEY') else "DEEPSEEK_API_KEY not set")
    print("Starting Flask application...")
    app.run(host=Config.HOST, port=Config.PORT, debug=True)
