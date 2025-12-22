import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY")
    PROJECT_NAME: str = "SDP OCR Backend"

settings = Settings()