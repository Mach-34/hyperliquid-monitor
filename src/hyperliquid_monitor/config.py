import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get addresses from environment
ADDRESSES = [addr.strip() for addr in os.getenv("MONITORED_ADDRESSES", "").split(",") if addr.strip()]

# Database configuration
DB_PATH = os.getenv("DB_PATH", "trades.db")