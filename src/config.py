"""Application settings loaded from environment variables / .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Store configuration settings for the HubSpot importer."""

    hubspot_access_token: str = ""
    base_url: str = "https://api.hubapi.com"
    rate_limit_delay: float = 0.15  # seconds between HubSpot API calls to stay within rate limits

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
