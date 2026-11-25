"""Limite de intentos en el login y en los formularios publicos.

Auditoria de seguridad del 2026-11-25 (B1, B2, B3): el login dejaba probar
claves sin freno, y `POST /leads/` (que manda un correo por envio) y
`POST /services/requests` no tenian limite.
"""

from tests.conftest import API


def test_el_login_se_frena_tras_diez_intentos_fallidos(http_client, seed_data):
    cuerpo = {"email": "test-admin@ninjasec.local", "password": "clave-equivocada"}
    codigos = [http_client.post(f"{API}/auth/login", json=cuerpo).status_code for _ in range(10)]
    assert set(codigos) == {401}, codigos

    r = http_client.post(f"{API}/auth/login", json=cuerpo)
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) >= 1


def test_frenado_ni_la_clave_correcta_entra(http_client, seed_data):
    """Si la clave buena pasara, el limite no serviria contra quien adivina."""
    malo = {"email": "test-admin@ninjasec.local", "password": "clave-equivocada"}
    for _ in range(10):
        http_client.post(f"{API}/auth/login", json=malo)
    bueno = {"email": "test-admin@ninjasec.local", "password": "testpassword123"}
    assert http_client.post(f"{API}/auth/login", json=bueno).status_code == 429


def test_un_login_normal_no_se_frena(http_client, seed_data):
    bueno = {"email": "test-admin@ninjasec.local", "password": "testpassword123"}
    for _ in range(3):
        assert http_client.post(f"{API}/auth/login", json=bueno).status_code == 200


def test_el_formulario_de_leads_se_frena_al_sexto_envio(http_client):
    lead = {
        "company_name": "Empresa Prueba",
        "contact_name": "Persona Prueba",
        "email": "persona@example.com",
        "message": "Quiero una auditoria",
    }
    for i in range(5):
        r = http_client.post(f"{API}/leads/", json=lead)
        assert r.status_code == 201, (i, r.text)
    assert http_client.post(f"{API}/leads/", json=lead).status_code == 429


def test_las_solicitudes_de_servicio_se_frenan_al_sexto_envio(http_client):
    """El limite actua antes de validar: no hace falta un servicio real."""
    codigos = [
        http_client.post(f"{API}/services/requests", json={}).status_code for _ in range(6)
    ]
    assert 429 not in codigos[:5], codigos
    assert codigos[5] == 429, codigos
