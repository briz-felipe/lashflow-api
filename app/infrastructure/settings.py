from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./lashflow.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    ADMIN_EMAIL: str | None = None

    # OAuth2 client credentials (optional)
    # When set, /auth/token requires client_id + client_secret matching these values.
    # Use this to restrict which clients (e.g. your Next.js backend) can exchange
    # username/password for tokens. Leave unset to disable client validation.
    OAUTH2_CLIENT_ID: str | None = None
    OAUTH2_CLIENT_SECRET: str | None = None

    # Key for encrypting Apple App-Specific Passwords in the DB.
    APPLE_ENCRYPTION_KEY: str | None = None

    # Set True in production (requires HTTPS for Secure cookie flag)
    COOKIE_SECURE: bool = False

    # CORS — comma-separated exact origins allowed to call the API
    # Example: "http://localhost:3000,https://lashflow.vercel.app"
    CORS_ORIGINS: str = "http://localhost:3000"

    # CORS regex — for wildcard patterns (Vercel previews, etc.)
    # Example: "https://lashflow-[a-zA-Z0-9-]+\\.vercel\\.app"
    CORS_ORIGIN_REGEX: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def oauth2_client_auth_enabled(self) -> bool:
        """True only when both client_id and client_secret are non-empty strings."""
        return bool(self.OAUTH2_CLIENT_ID and self.OAUTH2_CLIENT_SECRET)

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()
