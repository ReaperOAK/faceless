import os
import logging
from dotenv import load_dotenv
from app import create_app

# Load environment variables from .env file if exists
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

# Determine environment
env = os.environ.get('FLASK_ENV', 'development')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# Create Flask application
app = create_app(env)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=(env == 'development'))