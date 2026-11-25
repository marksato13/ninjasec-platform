from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Ninja Tech"
    app_version: str = "0.2.0"
    api_prefix: str = "/api/v1"
    app_env: str = "development"

    # Modo produccion. Se activa por cualquiera de las dos vias:
    #   APP_ENV=production   -> convencion 12-factor, la que ya existia
    #   IS_PRODUCTION=true   -> la que setea infra/docker-compose.prod.yml
    #
    # Antes esto era solo una @property derivada de app_env, asi que el
    # IS_PRODUCTION del compose de produccion no tenia campo que lo
    # recibiera y pydantic lo ignoraba en silencio: is_production devolvia
    # False en produccion y las guardas de app/main.py nunca se disparaban.
    # Se mantiene como campo para que ambas grafias funcionen y para que
    # settings.is_production siga leyendose igual en todo el codigo.
    is_production: bool = False

    seed_on_startup: bool = True

    # Clave con la que se crean TODOS los usuarios de siembra. Si se deja
    # vacia, seed.py usa las claves de desarrollo que estan escritas en el
    # codigo -- y se niega a sembrar si el entorno es de produccion.
    #
    # Existe porque el repositorio va a ser publico: con las claves solo en
    # el codigo, cualquiera que despliegue sin poner APP_ENV=production
    # levanta un admin con credencial conocida en una URL publica.
    #
    # Nunca se registra en el log ni se devuelve por la API.
    seed_password: str | None = None

    # Capsulas de funcionalidad encendidas, separadas por comas.
    # Vacio = solo las que estan activas por defecto en app/core/features.py.
    #
    # Hoy existe "telemetria": conectores, recoleccion, hardening, puntuacion
    # de riesgo e indice de salud. Esta APAGADA porque los conectores son
    # simulados y el informe SOC corre sobre ese dato inventado.
    #
    # Un nombre que no exista rompe el arranque a proposito: una errata aqui
    # es silenciosa de la peor manera, porque crees que encendiste algo y no.
    capsulas_activas: str | None = None
    database_url: str = "postgresql+psycopg://postgres:123456@localhost:5432/ninjasec"
    jwt_secret_key: str = "change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3010,http://127.0.0.1:3010,http://localhost:3018,http://127.0.0.1:3018,http://localhost:3014,http://127.0.0.1:3014,http://localhost:3012,http://127.0.0.1:3012"

    storage_path: str = "./storage"
    storage_max_file_size: int = 10 * 1024 * 1024

    # G-06: backend distribuido del rate limiter (app/common/rate_limit.py).
    # Vacio por defecto -> limitador en memoria, un solo proceso (dev/CI).
    # Con esto configurado y Redis alcanzable, el limite se comparte entre
    # workers/replicas. Si Redis se cae despues de arrancar, el limitador
    # falla abierto -- ver el docstring del modulo.
    redis_url: str = ""

    # Auditoria 2026-11-25 (B1): intentos de login por IP cada 5 minutos.
    # Solo el e2e del CI lo sube, porque inicia sesion muchas veces seguidas.
    login_rate_limit_max: int = 10

    # Login con Google (issue #83). Vacio por defecto -> el boton de Google
    # no aparece en el frontend (GET /auth/google/config reporta enabled=false)
    # y POST /auth/google responde 503. El client_id NO es secreto -- viaja
    # al frontend via ese mismo endpoint publico, es el mismo valor que
    # cualquier pagina "Iniciar sesion con Google" expone en su HTML. No hay
    # client_secret ni redirect_uri configurables porque el flujo verifica el
    # ID token que entrega Google Identity Services directo en el navegador
    # (ver docstring de AuthService.authenticate_google) -- no hace el
    # intercambio de codigo de autorizacion contra el backend de Google.
    google_client_id: str = ""

    # Notificaciones por correo (08-P-06 / 15-P-07). Vacio por defecto -> el
    # modulo app/common/email.py queda inerte: no manda nada y no falla. Es
    # lo correcto en dev y CI, donde nadie quiere un SMTP de verdad.
    # Agnostico de proveedor a proposito: Gmail, Resend, Brevo, Mailgun, SES
    # y un servidor propio hablan todos SMTP, asi que cambiar de proveedor es
    # editar el .env. NUNCA loguear smtp_password.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout: int = 10
    # Buzon que recibe los avisos. Sin esto tampoco se envia nada: no hay
    # destinatario por defecto a proposito.
    notify_email: str = ""

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

    @model_validator(mode="after")
    def _derivar_modo_produccion(self) -> "Settings":
        """APP_ENV=production tambien enciende is_production.

        Las dos grafias conviven a proposito: el compose de produccion usa
        IS_PRODUCTION y el resto del ecosistema espera APP_ENV. Cualquiera
        de las dos basta; nunca apaga la otra.
        """
        if self.app_env.lower() == "production":
            self.is_production = True
        return self


settings = Settings()
