import os

class APIConfig:
    def __init__(self):
        # Database
        self.DATABASE_PATH = "gifts.db"
        
        # API
        self.API_HOST = "0.0.0.0"
        self.API_PORT = 8000
        
        # S3 Configuration (optional for API)
        self.S3_BUCKET = os.getenv("S3_BUCKET", "")
        self.AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.AWS_REGION = os.getenv("AWS_REGION", "us-east-1")