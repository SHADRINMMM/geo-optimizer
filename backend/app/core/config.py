from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "changeme"
    DOMAIN: str = "ai.causabi.com"

    # Database
    DATABASE_URL: str

    # Cloudflare R2
    S3_BUCKET_NAME: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_ENDPOINT_URL: str
    PUBLIC_R2_PUBLIC_BASE_URL: str

    # AI
    GOOGLE_API_KEY: str
    LLM_MODEL: str = "gemini-2.0-flash"
    AWS_BEDROCK_API_KEY: str = ""
    AWS_BEDROCK_REGION: str = "us-east-1"
    CLAUDE_MODEL: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    OPENAI_API_KEY: str = ""
    YANDEX_API_KEY: str = ""
    YANDEX_FOLDER_ID: str = ""

    # Monitoring
    # Comma-separated list of engines to use: gemini,chatgpt,yandex,google_ai,claude
    MONITOR_ENGINES: str = "gemini,google_ai,claude"
    # How many expanded queries to generate per target query (0 = disabled)
    MONITOR_QUERY_EXPANSION: int = 3
    # Max queries per site per monitoring run
    MONITOR_MAX_QUERIES: int = 10

    # Auth
    PROPELAUTH_AUTH_URL: str
    PROPELAUTH_API_KEY: str
    PROPELAUTH_PUBLIC_KEY: str = ""

    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379/0"

    # External APIs
    GOOGLE_PLACES_API_KEY: str = ""
    INDEXNOW_KEY: str = ""

    # Email
    SENDGRID_API_KEY: str = ""

    # Analytics
    POSTHOG_API_KEY: str = ""
    POSTHOG_PROJECT_ID: str = ""
    POSTHOG_API_HOST: str = "https://us.posthog.com"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
