from dotenv import load_dotenv
import os

load_dotenv()

# fetch env vars, with optional defaults
DB_USER     = os.getenv("DB_USER", "fallback_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "fallback_password")
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "3306")
DB_NAME     = os.getenv("DB_NAME", "traffic_detection")
