import os

class Config:
    def __init__(self):
        self.BOT_TOKEN = os.getenv("BOT_TOKEN", "")
        self.WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:5000")
        
        # S3 Configuration
        self.S3_BUCKET = os.getenv("S3_BUCKET", "")
        self.AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
        
        # Database
        self.DATABASE_PATH = "gifts.db"
        
        # API
        self.API_HOST = "0.0.0.0"
        self.API_PORT = 8000
        
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN environment variable is required")
        
        if not all([self.S3_BUCKET, self.AWS_ACCESS_KEY_ID, self.AWS_SECRET_ACCESS_KEY]):
            raise ValueError("S3 credentials (S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) are required")
