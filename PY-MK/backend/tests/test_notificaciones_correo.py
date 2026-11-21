"""Avisos por correo de lead y postulacion (08-P-06 / 15-P-07).

Lo que de verdad importa verificar aqui no es que el correo salga -- eso
depende de un SMTP real-- sino que **el fallo del correo nunca cueste el
dato**. Un lead que entra y se pierde porque el servidor de correo estaba
caido seria peor que no notificar en absoluto.

Por eso la mayoria de estos tests comprueban el camino de fallo.
"""

import smtplib
from unittest.mock import patch

import pytest

from app.common import email as email_mod
from tests.conftest import API


# ---------------------------------------------------------------------------
# El modulo es inerte sin configuracion
# ---------------------------------------------------------------------------


def test_sin_configurar_no_esta_activo():
    """Dev y CI no tienen SMTP: el modulo debe callarse, no fallar."""
    assert email_mod.correo_configurado() is False
    assert email_mod.enviar_correo("asunto", "cuerpo") is False


def test_hace_falta_host_y_destinatario(monkeypatch):
    """Configurar solo la mitad no activa nada."""
    monkeypatch.setattr(email_mod.settings, "smtp_host", "smtp.test")
    monkeypatch.setattr(email_mod.settings, "notify_email", "")
    assert email_mod.correo_configurado() is False

    monkeypatch.setattr(email_mod.settings, "smtp_host", "")
    monkeypatch.setattr(email_mod.settings, "notify_email", "a@test.local")
    assert email_mod.correo_configurado() is False


# ---------------------------------------------------------------------------
# El camino de fallo: lo importante
# ---------------------------------------------------------------------------


@pytest.fixture
def smtp_configurado(monkeypatch):
    monkeypatch.setattr(email_mod.settings, "smtp_host", "smtp.test")
    monkeypatch.setattr(email_mod.settings, "smtp_port", 587)
    monkeypatch.setattr(email_mod.settings, "smtp_user", "")
    monkeypatch.setattr(email_mod.settings, "notify_email", "avisos@test.local")
    monkeypatch.setattr(email_mod.settings, "smtp_from", "web@test.local")
    monkeypatch.setattr(email_mod.settings, "smtp_use_ssl", False)
    monkeypatch.setattr(email_mod.settings, "smtp_use_tls", False)


def test_un_smtp_caido_no_lanza(smtp_configurado):
    with patch.object(
        email_mod.smtplib, "SMTP", side_effect=smtplib.SMTPConnectError(421, "nope")
    ):
        assert email_mod.enviar_correo("asunto", "cuerpo") is False


def test_un_timeout_no_lanza(smtp_configurado):
    with patch.object(email_mod.smtplib, "SMTP", side_effect=TimeoutError):
        assert email_mod.enviar_correo("asunto", "cuerpo") is False


def test_el_lead_se_guarda_aunque_el_correo_falle(http_client, smtp_configurado):
    """El test que justifica todo este archivo.

    `/leads/` es publico: es el formulario de contacto de la web. Si un SMTP
    caido tumbara esta peticion, perderias clientes potenciales sin enterarte.
    """
    with patch.object(
        email_mod.smtplib, "SMTP", side_effect=smtplib.SMTPException("caido")
    ):
        respuesta = http_client.post(
            f"{API}/leads/",
            json={
                "company_name": "PYME de prueba",
                "contact_name": "Ana Quispe",
                "email": "ana@pymeprueba.com",
                "message": "Quiero una auditoria",
            },
        )

    assert respuesta.status_code == 201
    assert respuesta.json()["company_name"] == "PYME de prueba"


def test_la_postulacion_se_guarda_aunque_el_correo_falle(http_client, smtp_configurado):
    with patch.object(
        email_mod.smtplib, "SMTP", side_effect=smtplib.SMTPException("caido")
    ):
        respuesta = http_client.post(
            f"{API}/job-applications/",
            json={
                "full_name": "Luis Mamani",
                "email": "luis.correo.falla@ejemplo.com",
                "desired_role": "SOC Analyst",
            },
        )

    assert respuesta.status_code == 201


# ---------------------------------------------------------------------------
# El camino feliz
# ---------------------------------------------------------------------------


def test_el_alta_de_lead_dispara_el_aviso(http_client, smtp_configurado):
    with patch.object(email_mod, "enviar_correo", return_value=True) as enviar:
        http_client.post(
            f"{API}/leads/",
            json={
                "company_name": "Distribuidora Sur",
                "contact_name": "Rosa Flores",
                "email": "rosa@distribuidorasur.com",
                "phone": "999888777",
                "message": "Necesitamos revisar el firewall",
            },
        )

    assert enviar.called
    asunto, cuerpo = enviar.call_args[0][0], enviar.call_args[0][1]
    assert "Distribuidora Sur" in asunto
    # El cuerpo tiene que traer lo necesario para actuar sin abrir el panel.
    assert "rosa@distribuidorasur.com" in cuerpo
    assert "999888777" in cuerpo
    assert "revisar el firewall" in cuerpo


def test_el_cuerpo_tolera_los_campos_opcionales_vacios(smtp_configurado):
    """phone y message son opcionales; no pueden romper el formateo."""
    with patch.object(email_mod, "enviar_correo", return_value=True) as enviar:
        email_mod.avisar_lead_nuevo(
            empresa="Sin Datos SAC",
            contacto="Alguien",
            email="x@test.local",
            telefono=None,
            mensaje=None,
        )

    cuerpo = enviar.call_args[0][1]
    assert "(sin mensaje)" in cuerpo
    assert "None" not in cuerpo


def test_el_aviso_de_postulacion_lleva_lo_necesario(smtp_configurado):
    with patch.object(email_mod, "enviar_correo", return_value=True) as enviar:
        email_mod.avisar_postulacion_nueva(
            nombre="Carla Ruiz",
            email="carla@test.local",
            puesto="Pentester",
            resumen="3 anios en redes",
        )

    asunto, cuerpo = enviar.call_args[0][0], enviar.call_args[0][1]
    assert "Carla Ruiz" in asunto
    assert "carla@test.local" in cuerpo
    assert "Pentester" in cuerpo


def test_no_se_envia_a_nadie_si_falta_el_destinatario(monkeypatch):
    """Sin NOTIFY_EMAIL no hay a quien avisar: no se intenta conectar."""
    monkeypatch.setattr(email_mod.settings, "smtp_host", "smtp.test")
    monkeypatch.setattr(email_mod.settings, "notify_email", "")

    with patch.object(email_mod.smtplib, "SMTP") as smtp:
        assert email_mod.enviar_correo("asunto", "cuerpo") is False
        assert not smtp.called
