from contextlib import asynccontextmanager
from pathlib import Path

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
