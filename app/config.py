import os
from dataclasses import dataclass


@dataclass
class Config:
    BOT_TOKEN: str
    WEBAPP_URL: str
    DB_PATH: str = os.getenv("DB_PATH", "/data/bot.db")

    S3_BUCKET: str = os.getenv("S3_BUCKET", "")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

    # Will be set on startup
    BOT_USERNAME: str | None = None

    @classmethod
    def load(cls):
        token = os.getenv("BOT_TOKEN", "")
        webapp_url = os.getenv("WEBAPP_URL", "")
        if not token or not webapp_url:
            raise RuntimeError("BOT_TOKEN and WEBAPP_URL must be set in environment")
        return cls(
            BOT_TOKEN=token,
            WEBAPP_URL=webapp_url,
            DB_PATH=os.getenv("DB_PATH", "/data/bot.db"),
            S3_BUCKET=os.getenv("S3_BUCKET", ""),
            AWS_ACCESS_KEY_ID=os.getenv("AWS_ACCESS_KEY_ID", ""),
            AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            AWS_REGION=os.getenv("AWS_REGION", "us-east-1"),
        )


cfg = Config.load()
