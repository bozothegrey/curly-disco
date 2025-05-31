import logging
import sys
from datetime import datetime

def setup_logging():
    """Configure comprehensive logging for the application"""
    
    # Create custom formatter for conversation events
    class ConversationFormatter(logging.Formatter):
        def format(self, record):
            # Add timestamp and custom formatting for conversation events
            if hasattr(record, 'user_id'):
                record.msg = f"[USER: {record.user_id}] {record.msg}"
            return super().format(record)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('conversations.log') if not sys.stdout.isatty() else logging.NullHandler()
        ]
    )
    
    # Set specific log levels
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Create conversation-specific logger
    conv_logger = logging.getLogger('conversations')
    conv_handler = logging.FileHandler('conversation_events.log')
    conv_formatter = ConversationFormatter(
        '%(asctime)s - CONVERSATION - %(levelname)s - %(message)s'
    )
    conv_handler.setFormatter(conv_formatter)
    conv_logger.addHandler(conv_handler)
    conv_logger.setLevel(logging.INFO)
