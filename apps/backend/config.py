from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:5173,https://contexia.online"

    @property
    def origins_list(self) -> List[str]:
        return self.ALLOWED_ORIGINS.split(",")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
