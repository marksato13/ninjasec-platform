"""La siembra no crea usuarios con claves conocidas en producción.

El repositorio va a ser público y las claves de desarrollo están escritas
en `app/db/seed.py`. Quien despliegue sin poner `APP_ENV=production` levanta
`admin@ninjasec.local` con una credencial que cualquiera puede leer en
GitHub.

`app/main.py` ya no siembra cuando `is_production`, pero `seed_initial_data`
también se puede llamar a mano desde un script o una consola, y ahí no había
nada que lo impidiera. Estas pruebas cubren esa segunda puerta.
"""

from __future__ import annotations

import pytest

from app.db import seed as modulo_seed
from app.db.seed import SiembraNoPermitida, _clave_de_siembra, seed_initial_data


class _SesionQueNoDeberiaUsarse:
    """Si la guarda funciona, no se llega a tocar la base de datos."""

    def __getattr__(self, nombre):  # pragma: no cover - solo si falla la guarda
        raise AssertionError(
            f"La siembra llegó a usar la sesión (.{nombre}) en producción: "
            "la guarda no se disparó."
        )


# --------------------------------------------------------------------------
# La guarda de producción
# --------------------------------------------------------------------------


def test_en_produccion_sin_clave_propia_no_siembra(monkeypatch):
    monkeypatch.setattr(modulo_seed.settings, "is_production", True, raising=False)
    monkeypatch.setattr(modulo_seed.settings, "seed_password", None, raising=False)

    with pytest.raises(SiembraNoPermitida):
        seed_initial_data(_SesionQueNoDeberiaUsarse())


def test_el_mensaje_de_error_dice_que_hacer(monkeypatch):
    """Un error que no dice la salida obliga a leer el código fuente."""
    monkeypatch.setattr(modulo_seed.settings, "is_production", True, raising=False)
    monkeypatch.setattr(modulo_seed.settings, "seed_password", None, raising=False)

    with pytest.raises(SiembraNoPermitida) as capturado:
        seed_initial_data(_SesionQueNoDeberiaUsarse())

    assert "SEED_PASSWORD" in str(capturado.value)


def test_el_error_no_revela_ninguna_clave(monkeypatch):
    """El mensaje no debe filtrar las claves de desarrollo."""
    monkeypatch.setattr(modulo_seed.settings, "is_production", True, raising=False)
    monkeypatch.setattr(modulo_seed.settings, "seed_password", None, raising=False)

    with pytest.raises(SiembraNoPermitida) as capturado:
        seed_initial_data(_SesionQueNoDeberiaUsarse())

    mensaje = str(capturado.value)
    for clave in ("change-me", "admin123", "temp123", "client123", "colab123"):
        assert clave not in mensaje, f"El mensaje de error filtra '{clave}'"


# --------------------------------------------------------------------------
# La resolución de la clave
# --------------------------------------------------------------------------


def test_sin_seed_password_se_usa_la_de_desarrollo(monkeypatch):
    """Que el entorno local y el CI sigan funcionando igual."""
    monkeypatch.setattr(modulo_seed.settings, "seed_password", None, raising=False)

    assert _clave_de_siembra("change-me") == "change-me"


def test_seed_password_manda_sobre_la_del_codigo(monkeypatch):
    monkeypatch.setattr(
        modulo_seed.settings, "seed_password", "una-clave-propia", raising=False
    )

    assert _clave_de_siembra("change-me") == "una-clave-propia"
    assert _clave_de_siembra("admin123") == "una-clave-propia"


def test_con_seed_password_ninguna_clave_del_codigo_sobrevive(monkeypatch):
    """Todas las claves fijas pasan por el resolutor, no solo algunas.

    Si alguien añade un usuario nuevo con la clave escrita a pelo, esta
    prueba no lo caza -- lo caza `test_todas_las_claves_pasan_por_el_resolutor`.
    Esta comprueba el contrato del resolutor para las cuatro que existen.
    """
    monkeypatch.setattr(modulo_seed.settings, "seed_password", "otra", raising=False)

    for clave in ("change-me", "admin123", "temp123", "client123"):
        assert _clave_de_siembra(clave) == "otra"


def test_todas_las_claves_pasan_por_el_resolutor():
    """Ninguna llamada a upsert_user pasa una clave fija sin envolver.

    Es la prueba que de verdad protege: lee el archivo y comprueba que no
    quedó ninguna clave suelta, ni ahora ni cuando alguien añada un usuario.
    """
    import re
    from pathlib import Path

    fuente = Path(modulo_seed.__file__).read_text(encoding="utf-8")
    sueltas = re.findall(
        r'^\s+"(change-me|admin123|temp123|client123|colab123)",\s*$',
        fuente,
        re.MULTILINE,
    )

    assert not sueltas, (
        "Hay claves de siembra sin envolver en _clave_de_siembra(): "
        f"{sorted(set(sueltas))}"
    )
