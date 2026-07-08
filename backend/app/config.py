from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/sunwai"
    gemini_api_key: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    demo_inject_token: str = ""

    structuring_model: str = "gemini-flash-latest"
    ranking_model: str = "gemini-pro-latest"
    embedding_model: str = "gemini-embedding-001"


settings = Settings()
