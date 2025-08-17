from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AI-Augmented PM System"
    # DB_URL and other settings will be added later

settings = Settings()
