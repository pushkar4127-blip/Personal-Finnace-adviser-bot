import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'instance', 'finance_bot.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    AI_PROVIDER = os.environ.get("AI_PROVIDER", "none").lower()
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

    NGROK_AUTHTOKEN = os.environ.get("NGROK_AUTHTOKEN", "")
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
