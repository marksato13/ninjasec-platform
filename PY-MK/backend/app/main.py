from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.core.error_handlers import register_exception_handlers
from app.db.seed import seed_initial_data
from app.db.session import SessionLocal


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.seed_on_startup and not settings.is_production:
        db = SessionLocal()
        try:
            seed_initial_data(db)
        finally:
            db.close()
    yield


if settings.is_production:
    if settings.jwt_secret_key == "change-this-secret-in-production":
        raise RuntimeError("JWT_SECRET_KEY must be set in production")
    if not settings.cors_origin_list:
        raise RuntimeError("CORS_ORIGINS must be set in production")


# En produccion no se publica la documentacion interactiva. No es codigo
# fuente, pero Swagger expone el plano completo de la API --cada endpoint,
# cada esquema, cada campo y cada validacion-- y eso es reconocimiento
# gratis para un atacante. En dev sigue disponible en /docs como siempre.
_docs_publicos = not settings.is_production

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="NinjaSec platform API",
    lifespan=lifespan,
    docs_url="/docs" if _docs_publicos else None,
    redoc_url="/redoc" if _docs_publicos else None,
    openapi_url="/openapi.json" if _docs_publicos else None,
)

@app.middleware("http")
async def _redirecciones_relativas(request, call_next):
    """Convierte la cabecera Location de absoluta a relativa.

    FastAPI construye el Location de sus redirecciones -- la de `redirect_slashes`,
    sobre todo -- a partir del Host de la peticion. Detras del proxy de Next, ese
    Host es `backend:8024`: el nombre del servicio DENTRO de la red de Docker.

    Eso produce dos problemas a la vez:

    1. **Fuga de topologia.** Pedir `/api/v1/clients` sin barra final devuelve
       `Location: http://backend:8024/api/v1/clients/`, y le regala a cualquiera
       la estructura interna. Lo detecto una prueba E2E del PR #128.
    2. **El redirect no funciona.** Ese nombre no resuelve desde fuera, asi que
       cualquier cliente que siga la redireccion falla con un error de DNS. El
       frontend se salva solo porque siempre usa barra final.

    Un Location relativo lo resuelve el propio cliente contra el host por el que
    entro, que es el correcto por definicion. Es lo que recomienda el RFC 7231
    desde que dejo de exigir URI absolutas.
    """
    respuesta = await call_next(request)
    if 300 <= respuesta.status_code < 400:
        destino = respuesta.headers.get("location")
        if destino:
            partes = urlsplit(destino)
            if partes.netloc:
                respuesta.headers["location"] = (
                    urlunsplit(("", "", partes.path, partes.query, partes.fragment))
                    or "/"
                )
    return respuesta


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(api_router, prefix=settings.api_prefix)
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/", tags=["root"])
def root() -> dict[str, object]:
    return {
        "message": "Welcome to NinjaSec backend",
        "health": "/health",
        "docs": "/docs",
        "api": settings.api_prefix,
    }


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
