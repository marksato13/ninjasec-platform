from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NinjaSec"
    app_version: str = "0.2.0"
    api_prefix: str = "/api/v1"
    app_env: str = "development"
    seed_on_startup: bool = True
    database_url: str = "postgresql+psycopg://postgres:123456@localhost:5432/ninjasec"
    jwt_secret_key: str = "change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3010,http://127.0.0.1:3010,http://localhost:3018,http://127.0.0.1:3018,http://localhost:3014,http://127.0.0.1:3014,http://localhost:3012,http://127.0.0.1:3012"

    storage_path: str = "./storage"
    storage_max_file_size: int = 10 * 1024 * 1024

    # 30-P2: reputación externa de IPs -- vacío por defecto, degrada a modo
    # simulado (nunca rompe) cuando no hay key configurada. Nunca loguear
    # el valor de estos campos.
    abuseipdb_api_key: str = ""
    virustotal_api_key: str = ""
    greynoise_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


settings = Settings()
