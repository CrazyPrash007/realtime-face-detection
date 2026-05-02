from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]
    MAX_FRAME_BYTES: int = 1_000_000  # 1MB cap against DoS
    MAX_WS_CONNECTIONS: int = 10

    class Config:
        env_file = ".env"

settings = Settings()
