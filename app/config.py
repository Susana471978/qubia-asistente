from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "Qubia Asistente"

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "qubia"

    groq_api_key: str = ""
    groq_model_default: str = "llama-4-scout-17b-16e-instruct"

    jwt_secret: str = "cambiar-en-produccion"
    jwt_alg: str = "HS256"
    jwt_expire_min: int = 480

    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "asistente@qubia.es"

    tenant_cache_ttl: int = 300
    admin_allowed_origins: str = "http://localhost:5173"

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"

    @property
    def admin_origins(self) -> list[str]:
        return [o.strip() for o in self.admin_allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
