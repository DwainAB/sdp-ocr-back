import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY")
    PROJECT_NAME: str = "SDP OCR Backend"

    # OpenAI (répartition intelligente des quantités de notes olfactives)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Configuration SMTP Gmail
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "SDP OCR")
    SMTP_CC_EMAIL: str = os.getenv("SMTP_CC_EMAIL", "")

    # URL du serveur pour les fichiers statiques
    SERVER_URL: str = os.getenv("SERVER_URL", "http://localhost:8000")

    # Stockage fichiers : "local" ou "s3"
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "")
    AWS_S3_REGION: str = os.getenv("AWS_S3_REGION", "us-east-1")
    AWS_S3_ENDPOINT: str = os.getenv("AWS_S3_ENDPOINT", "")  # laisser vide pour AWS natif

settings = Settings()