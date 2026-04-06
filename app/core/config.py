from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Stocky"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    llm_provider: str = "openrouter"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-5.4"
    openrouter_app_name: str = "Stocky"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "stocky"
    postgres_user: str = "stocky_user"
    postgres_password: str = "stocky_password"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def openrouter_enabled(self) -> bool:
        return bool(self.openrouter_api_key)


settings = Settings()
