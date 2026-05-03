from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # database
    DATABASE_URL: str
    # These are used by the Postgres Docker image, not directly by the app.
    # Making them optional avoids a ValidationError when they are absent.
    POSTGRES_USER: str = "faceuser"
    POSTGRES_PASSWORD: str = "strongpassword"
    POSTGRES_DB: str = "facesdb"

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
