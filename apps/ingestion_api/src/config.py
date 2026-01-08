"""Configuration for the Ingestion API."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Database (IMPORTANT: async SQLAlchemy URL)
    # Example: postgresql+asyncpg://user:pass@host:5432/dbname
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/stranger_beers"

    # Tally: which forms we accept
    tally_signup_form_id: str = ""
    tally_payment_form_id: str = ""

    # Tally webhook signature verification (recommended in production)
    verify_tally_signature: bool = False
    tally_signup_secret: str = ""
    tally_payment_secret: str = ""

    # Phone parsing
    # Used when users enter national-format numbers like "06..."
    default_phone_region: str = "NL"

    # Behavior flags
    # If true, any payment form submission counts as paid.
    # If false, you will map a "payment_status" field in the payment form and check it.
    payment_submission_means_paid: bool = True

    # Logging
    log_level: str = "INFO"
    log_json: bool = False


settings = Settings()
