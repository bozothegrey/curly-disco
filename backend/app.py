from flask import Flask
from flask_cors import CORS
from routes.chat_routes import chat_bp
from routes.conversation_routes import conversation_bp
from routes.health_routes import health_bp
from utils.logging_config import setup_logging
from config import Config

# Setup logging
setup_logging()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(chat_bp)
app.register_blueprint(conversation_bp)
app.register_blueprint(health_bp)

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT)
