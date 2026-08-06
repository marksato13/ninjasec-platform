"""Rate limiting del endpoint publico de postulaciones (15-P-05).

`POST /job-applications/` es el unico endpoint sin autenticacion. Sin
freno, inundar la tabla de postulaciones es trivial.
"""

import pytest

from app.modules.recruitment.routers.router import public_application_limit

API = "/api/v1"


@pytest.fixture(autouse=True)
def _limpiar_contadores():
    """Cada test parte de cero; si no, se contaminan entre si."""
    public_application_limit.limiter.reset()
    yield
    public_application_limit.limiter.reset()


def _postulacion(n: int) -> dict:
    return {
        "full_name": f"Candidato {n}",
        "email": f"candidato{n}@example.com",
        "position": "Analista SOC",
    }


def test_postular_sigue_siendo_publico(http_client):
    """El limite no puede romper el caso de uso: postular sin cuenta."""
    res = http_client.post(f"{API}/job-applications/", json=_postulacion(1))
    assert res.status_code == 201, res.text


def test_bloquea_tras_superar_el_limite(http_client):
    for n in range(5):
        res = http_client.post(f"{API}/job-applications/", json=_postulacion(n))
        assert res.status_code == 201, f"La peticion {n + 1} fallo: {res.text}"

    res = http_client.post(f"{API}/job-applications/", json=_postulacion(99))
    assert res.status_code == 429, (
        "El endpoint publico acepta peticiones ilimitadas: vector de inundacion"
    )
    assert "Retry-After" in res.headers


def test_el_limite_es_por_ip(http_client):
    """Una IP saturada no puede bloquear al resto de candidatos."""
    for n in range(5):
        http_client.post(
            f"{API}/job-applications/",
            json=_postulacion(n),
            headers={"X-Forwarded-For": "203.0.113.10"},
        )

    bloqueada = http_client.post(
        f"{API}/job-applications/",
        json=_postulacion(50),
        headers={"X-Forwarded-For": "203.0.113.10"},
    )
    assert bloqueada.status_code == 429

    otra = http_client.post(
        f"{API}/job-applications/",
        json=_postulacion(51),
        headers={"X-Forwarded-For": "198.51.100.20"},
    )
    assert otra.status_code == 201, (
        "Una IP abusiva esta bloqueando a candidatos legitimos"
    )


def test_el_limite_no_afecta_a_los_endpoints_autenticados(http_client, admin_token):
    """Agotar el limite publico no debe cerrar la bandeja del equipo."""
    for n in range(6):
        http_client.post(f"{API}/job-applications/", json=_postulacion(n))

    res = http_client.get(
        f"{API}/job-applications/", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
