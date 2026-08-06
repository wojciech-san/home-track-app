from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, read from environment variables or a .env file."""

    database_url: str = "sqlite:///./home_track.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
