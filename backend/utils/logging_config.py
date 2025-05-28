import logging
import sys

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log') if not sys.stdout.isatty() else logging.NullHandler()
        ]
    )
    
    # Set specific log levels for different modules
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

