from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # GitHub Models
    GITHUB_TOKEN: str
    GITHUB_MODEL: str = "gpt-4o-mini"
    GITHUB_API_BASE: str = "https://models.inference.ai.azure.com"

    USER_SERVICE_URL: str
    REPORT_SERVICE_URL: str
    NOTIFICATION_SERVICE_URL: str

    INTERNAL_SECRET: str

    ALERT_RADIUS_KM: float = 5.0

    PORT: int = 3004
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()