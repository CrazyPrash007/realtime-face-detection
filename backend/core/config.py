from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # database
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # backend
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]
    SECRET_KEY: str = "unsafe-default-key-for-dev"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"

    # security limits
    MAX_FRAME_BYTES: int = 1_000_000  # 1MB cap against DoS
    MAX_WS_CONNECTIONS: int = 10

    # cv tuning
    MEDIAPIPE_CONFIDENCE: float = 0.6

    class Config:
        env_file = ".env"

settings = Settings()
