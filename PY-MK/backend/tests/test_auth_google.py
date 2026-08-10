"""Login con Google (issue #83).

Verifica el ID token via mock -- no hay credenciales reales de Google
disponibles en este entorno (requiere registrar la app en Google Cloud
Console, accion humana). google.oauth2.id_token.verify_oauth2_token se
reemplaza por un doble de prueba; lo que se prueba es la logica propia
(politica de solo-cuentas-existentes, email_verified, errores), no la
libreria de Google en si.
"""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.modules.auth.services import auth_service as auth_service_module

API = "/api/v1"


@pytest.fixture(autouse=True)
def _sin_google_configurado_por_defecto():
    """Cada test parte del estado real por defecto (sin configurar)."""
    original = settings.google_client_id
    settings.google_client_id = ""
    yield
    settings.google_client_id = original


def test_google_config_deshabilitado_por_defecto(http_client, seed_data):
    response = http_client.get(f"{API}/auth/google/config")
    assert response.status_code == 200, response.text
    assert response.json() == {"enabled": False, "client_id": ""}


def test_google_login_sin_configurar_responde_503(http_client, seed_data):
    response = http_client.post(f"{API}/auth/google", json={"credential": "cualquier-cosa"})
    assert response.status_code == 503


def test_google_config_habilitado_expone_el_client_id(http_client, seed_data, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "fake-client-id.apps.googleusercontent.com")
    response = http_client.get(f"{API}/auth/google/config")
    assert response.status_code == 200, response.text
    assert response.json() == {"enabled": True, "client_id": "fake-client-id.apps.googleusercontent.com"}


def test_google_login_token_invalido_devuelve_401(http_client, seed_data, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "fake-client-id.apps.googleusercontent.com")

    def _explota(*_args, **_kwargs):
        raise ValueError("token malformado")

    monkeypatch.setattr(auth_service_module.google_id_token, "verify_oauth2_token", _explota)

    response = http_client.post(f"{API}/auth/google", json={"credential": "basura"})
    assert response.status_code == 401


def test_google_login_email_no_verificado_devuelve_401(http_client, seed_data, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "fake-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(
        auth_service_module.google_id_token,
        "verify_oauth2_token",
        lambda *_a, **_k: {"email": "test-admin@ninjasec.local", "email_verified": False},
    )

    response = http_client.post(f"{API}/auth/google", json={"credential": "token-valido-email-no-verificado"})
    assert response.status_code == 401


def test_google_login_sin_cuenta_existente_devuelve_404_sin_autocrear(http_client, seed_data, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "fake-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(
        auth_service_module.google_id_token,
        "verify_oauth2_token",
        lambda *_a, **_k: {"email": "nadie-tiene-esta-cuenta@ejemplo.com", "email_verified": True},
    )

    response = http_client.post(f"{API}/auth/google", json={"credential": "token-valido-email-desconocido"})
    assert response.status_code == 404
    assert "administrador" in response.json()["message"].lower(), (
        "el error debe guiar a contactar a un admin -- no debe insinuar que se puede autoregistrar"
    )


def test_google_login_con_cuenta_existente_emite_el_mismo_shape_que_login_normal(
    http_client, seed_data, monkeypatch
):
    monkeypatch.setattr(settings, "google_client_id", "fake-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(
        auth_service_module.google_id_token,
        "verify_oauth2_token",
        lambda *_a, **_k: {"email": "test-admin@ninjasec.local", "email_verified": True},
    )

    google_response = http_client.post(
        f"{API}/auth/google", json={"credential": "token-valido-cuenta-existente"}
    )
    assert google_response.status_code == 200, google_response.text
    google_body = google_response.json()

    password_response = http_client.post(
        f"{API}/auth/login",
        json={"email": "test-admin@ninjasec.local", "password": "testpassword123"},
    )
    password_body = password_response.json()

    assert set(google_body.keys()) == set(password_body.keys())
    assert google_body["redirect_to"] == password_body["redirect_to"]
    assert google_body["user"]["email"] == password_body["user"]["email"]
    assert google_body["token_type"] == "bearer"

    # El token que emite el login con Google debe servir igual que uno normal.
    me_response = http_client.get(
        f"{API}/auth/me", headers={"Authorization": f"Bearer {google_body['access_token']}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "test-admin@ninjasec.local"


def test_google_login_es_insensible_a_mayusculas_en_el_email(http_client, seed_data, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "fake-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(
        auth_service_module.google_id_token,
        "verify_oauth2_token",
        lambda *_a, **_k: {"email": "TEST-ADMIN@NINJASEC.LOCAL", "email_verified": True},
    )

    response = http_client.post(f"{API}/auth/google", json={"credential": "token-valido-mayusculas"})
    assert response.status_code == 200, response.text
    assert response.json()["user"]["email"] == "test-admin@ninjasec.local"
