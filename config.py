#config
import os
from dotenv import load_dotenv

# Load .env from the same directory as this file (simple dev use)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)
# alternatively: load_dotenv()  # will search current working directory

#FLASK
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

# Database configuration
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_NAME_ASSETMANAGER = os.getenv("DB_NAME_ASSETMANAGER")

# App configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEFAULT_JOB_STATUS = os.getenv("DEFAULT_JOB_STATUS", "active")