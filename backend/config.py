import os
from dotenv import load_dotenv

# Load .env only in local development (won't exist in Vercel)
load_dotenv()

# Get environment variables - will use Vercel env vars in production
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID") or os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET") or os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI") or os.environ.get("GOOGLE_REDIRECT_URI")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")