"""El flag de produccion debe encenderse por las dos grafias.

Historia: `is_production` era solo una @property derivada de `app_env`, pero
`infra/docker-compose.prod.yml` setea `IS_PRODUCTION: "true"`. Como no habia
ningun campo con ese nombre, pydantic-settings ignoraba la variable en
silencio y `settings.is_production` devolvia False **en produccion**. Eso
dejaba inertes las guardas de `app/main.py` que impiden arrancar con el
JWT_SECRET_KEY por defecto o sin CORS_ORIGINS.

Estos tests construyen `Settings` directamente con `_env_file=None` para no
heredar el `.env` del repo ni las variables que conftest.py deja puestas.
"""

from app.core.config import Settings


def _settings(**kwargs) -> Settings:
    # _env_file=None aisla el test de cualquier .env presente en disco.
    return Settings(_env_file=None, **kwargs)


def test_por_defecto_no_es_produccion():
    assert _settings().is_production is False


def test_is_production_true_lo_enciende():
    """La grafia que usa docker-compose.prod.yml."""
    assert _settings(is_production=True).is_production is True


def test_app_env_production_lo_enciende():
    """La grafia 12-factor, la que ya existia antes del arreglo."""
    assert _settings(app_env="production").is_production is True


def test_app_env_production_en_mayusculas_tambien():
    assert _settings(app_env="PRODUCTION").is_production is True


def test_las_dos_a_la_vez_no_se_apagan_entre_si():
    s = _settings(app_env="production", is_production=True)
    assert s.is_production is True


def test_app_env_no_apaga_el_flag_explicito():
    """IS_PRODUCTION=true manda aunque APP_ENV diga otra cosa.

    Es el caso real del compose de produccion, que setea IS_PRODUCTION pero
    no toca APP_ENV. Si el validador sobreescribiera con False, volveriamos
    exactamente al bug que esto arregla.
    """
    s = _settings(app_env="development", is_production=True)
    assert s.is_production is True


def test_otros_valores_de_app_env_no_encienden_produccion():
    for env in ("development", "testing", "staging", ""):
        assert _settings(app_env=env).is_production is False, env
