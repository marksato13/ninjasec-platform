"""Certificaciones con adjunto, validacion y equipo visible para el cliente.

La formacion se hace en plataformas externas; aqui se adjunta el certificado,
el super_admin lo valida y el cliente ve, en su proyecto, al personal asignado
con sus certificaciones validadas y vigentes (sin adjuntos ni datos internos).
"""

from __future__ import annotations

import importlib
from datetime import timedelta
from uuid import uuid4

import pytest

from app.core.security import create_access_token, hash_password
from app.core.time_utils import utcnow
from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.enums import CertificationStatus, RoleCode, UserStatus
from app.db.models.organization import Organization
from app.db.models.project import Project
from app.db.models.project_member import ProjectMember
from app.db.models.role import Role
from app.db.models.user import User
from app.db.models.user_certification import UserCertification
from tests.conftest import API

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _usuario(db, organization_id: int, rol: RoleCode) -> tuple[User, str]:
    role = db.query(Role).filter(Role.code == rol.value).first()
    if role is None:
        role = Role(code=rol.value, name=rol.value)
        db.add(role)
        db.flush()
    u = User(
        organization_id=organization_id,
        role_id=role.id,
        full_name=f"Persona {uuid4().hex[:6]}",
        email=f"cert-{uuid4().hex[:10]}@ninjasec.local",
        password_hash=hash_password("no-se-usa-123"),
        role_code=rol,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(u)
    db.commit()
    return u, create_access_token(u.email, extra={"role": rol.value})


def _certificacion(db, user_id: int, **kw) -> UserCertification:
    c = UserCertification(user_id=user_id, name=kw.pop("name", "Fortinet NSE 4"), issuer="Fortinet", **kw)
    db.add(c)
    db.commit()
    return c


def _subir(http_client, token, cert_id, contenido=PDF, tipo="application/pdf", nombre="nse4.pdf"):
    return http_client.post(
        f"{API}/user-certifications/{cert_id}/file",
        files={"file": (nombre, contenido, tipo)},
        headers=_auth(token),
    )


@pytest.fixture(autouse=True)
def _almacenamiento_temporal(tmp_path, monkeypatch):
    """Los archivos de prueba van a una carpeta temporal, no a ./storage."""
    from app.common.storage import storage

    monkeypatch.setattr(storage, "root", tmp_path.resolve())


@pytest.fixture
def org(seed_data):
    return seed_data["org"]


@pytest.fixture
def super_admin(db, org):
    return _usuario(db, org.id, RoleCode.SUPER_ADMIN)


@pytest.fixture
def colaborador(db, org):
    return _usuario(db, org.id, RoleCode.COLLABORATOR)


# --- Registrar y adjuntar -------------------------------------------------


def test_el_colaborador_registra_con_area_y_adjunta_su_certificado(http_client, colaborador):
    _, token = colaborador
    r = http_client.post(
        f"{API}/user-certifications/",
        json={"name": "AWS Cloud Practitioner", "issuer": "AWS", "area": "dev",
              "url": "https://www.credly.com/badges/abc"},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    cert = r.json()
    assert cert["area"] == "dev" and cert["status"] == "pending" and cert["has_file"] is False

    r = _subir(http_client, token, cert["id"])
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["has_file"] is True and cuerpo["file_type"] == "application/pdf"
    assert "file_key" not in cuerpo  # la clave de almacenamiento nunca sale

    r = http_client.get(f"{API}/user-certifications/{cert['id']}/file", headers=_auth(token))
    assert r.status_code == 200
    assert r.content == PDF
    assert r.headers["x-content-type-options"] == "nosniff"


def test_el_enlace_de_verificacion_debe_ser_web(http_client, colaborador):
    _, token = colaborador
    r = http_client.post(
        f"{API}/user-certifications/",
        json={"name": "CCNA", "url": "javascript:alert(1)"},
        headers=_auth(token),
    )
    assert r.status_code == 422


@pytest.mark.parametrize(
    "contenido,tipo,nombre",
    [
        (b"MZ\x90\x00 ejecutable", "application/pdf", "falso.pdf"),  # firma no coincide
        (b"<html><script>x</script>", "text/html", "x.html"),        # tipo no permitido
        (PDF, "application/msword", "nse4.doc"),                      # Word no es certificado
    ],
)
def test_archivo_invalido_da_415(http_client, db, colaborador, contenido, tipo, nombre):
    user, token = colaborador
    cert = _certificacion(db, user.id)
    assert _subir(http_client, token, cert.id, contenido, tipo, nombre).status_code == 415


def test_archivo_demasiado_grande_da_413(http_client, db, colaborador):
    user, token = colaborador
    cert = _certificacion(db, user.id)
    grande = b"%PDF-" + b"0" * (5 * 1024 * 1024 + 10)
    assert _subir(http_client, token, cert.id, grande).status_code == 413


def test_reemplazar_el_archivo_devuelve_la_validacion_a_pendiente(http_client, db, colaborador):
    user, token = colaborador
    cert = _certificacion(db, user.id, status=CertificationStatus.APPROVED)
    r = _subir(http_client, token, cert.id, PNG, "image/png", "nse4.png")
    assert r.status_code == 200
    assert r.json()["status"] == "pending"


# --- Quien ve el adjunto ---------------------------------------------------


def test_otro_colaborador_no_ve_ni_sube_el_certificado_ajeno(http_client, db, org, colaborador):
    duenio, _ = colaborador
    _, token_otro = _usuario(db, org.id, RoleCode.COLLABORATOR)
    cert = _certificacion(db, duenio.id)
    assert http_client.get(f"{API}/user-certifications/{cert.id}/file", headers=_auth(token_otro)).status_code == 404
    assert _subir(http_client, token_otro, cert.id).status_code == 404


def test_el_admin_de_otra_organizacion_recibe_404(http_client, db, colaborador):
    duenio, token = colaborador
    cert = _certificacion(db, duenio.id)
    assert _subir(http_client, token, cert.id).status_code == 200
    otra = Organization(name=f"Otra {uuid4().hex[:6]}", slug=f"otra-{uuid4().hex[:8]}")
    db.add(otra)
    db.commit()
    _, token_ajeno = _usuario(db, otra.id, RoleCode.SUPER_ADMIN)
    assert http_client.get(f"{API}/user-certifications/{cert.id}/file", headers=_auth(token_ajeno)).status_code == 404


def test_el_admin_de_la_organizacion_descarga_para_revisar(http_client, db, colaborador, admin_token):
    duenio, token = colaborador
    cert = _certificacion(db, duenio.id)
    assert _subir(http_client, token, cert.id).status_code == 200
    assert http_client.get(f"{API}/user-certifications/{cert.id}/file", headers=_auth(admin_token)).status_code == 200


# --- Validar ----------------------------------------------------------------


def test_solo_el_super_admin_valida_y_el_rechazo_exige_motivo(http_client, db, colaborador, super_admin, admin_token):
    duenio, token_colab = colaborador
    _, token_super = super_admin
    cert = _certificacion(db, duenio.id)
    url = f"{API}/user-certifications/{cert.id}/verify"
    for token in (token_colab, admin_token):
        assert http_client.post(url, json={"status": "approved"}, headers=_auth(token)).status_code == 403
    assert http_client.post(url, json={"status": "rejected"}, headers=_auth(token_super)).status_code == 422
    r = http_client.post(url, json={"status": "rejected", "rejection_reason": "Ilegible"}, headers=_auth(token_super))
    assert r.status_code == 200 and r.json()["rejection_reason"] == "Ilegible"
    r = http_client.post(url, json={"status": "approved"}, headers=_auth(token_super))
    assert r.status_code == 200 and r.json()["status"] == "approved"


def test_la_matriz_es_solo_para_admins_y_solo_lleva_lo_validado(http_client, db, org, colaborador, admin_token):
    duenio, token_colab = colaborador
    _certificacion(db, duenio.id, name="Validada", status=CertificationStatus.APPROVED, area="sec")
    _certificacion(db, duenio.id, name="Pendiente")
    _certificacion(db, duenio.id, name="Vencida", status=CertificationStatus.APPROVED,
                   expires_at=utcnow() - timedelta(days=2))
    assert http_client.get(f"{API}/user-certifications/matrix", headers=_auth(token_colab)).status_code == 403
    r = http_client.get(f"{API}/user-certifications/matrix", headers=_auth(admin_token))
    assert r.status_code == 200
    fila = next(f for f in r.json() if f["user_id"] == duenio.id)
    assert [c["name"] for c in fila["certifications"]] == ["Validada"]


# --- El cliente ve al equipo de SU proyecto ------------------------------


def _cliente_con_proyecto(db, org_id: int):
    cliente = Client(organization_id=org_id, company_name=f"Pyme {uuid4().hex[:6]}")
    db.add(cliente)
    db.flush()
    user, token = _usuario(db, org_id, RoleCode.CLIENT)
    db.add(ClientProfile(client_id=cliente.id, user_id=user.id))
    proyecto = Project(organization_id=org_id, client_id=cliente.id, name="Diagnóstico de red")
    db.add(proyecto)
    db.commit()
    return proyecto, token


def test_el_cliente_ve_solo_certificaciones_validadas_y_vigentes_sin_adjuntos(http_client, db, org, colaborador):
    tecnico, _ = colaborador
    proyecto, token_cliente = _cliente_con_proyecto(db, org.id)
    db.add(ProjectMember(project_id=proyecto.id, user_id=tecnico.id, role_in_project="Técnico de redes"))
    _certificacion(db, tecnico.id, name="Fortinet NSE 4", status=CertificationStatus.APPROVED,
                   credential_id="SECRETO-123", url="https://training.fortinet.com/verify/x",
                   file_key="certifications/1/x.pdf", file_name="nse4.pdf")
    _certificacion(db, tecnico.id, name="En revisión")
    _certificacion(db, tecnico.id, name="Rechazada", status=CertificationStatus.REJECTED)
    _certificacion(db, tecnico.id, name="Vencida", status=CertificationStatus.APPROVED,
                   expires_at=utcnow() - timedelta(days=1))
    no_miembro, _ = _usuario(db, org.id, RoleCode.COLLABORATOR)
    _certificacion(db, no_miembro.id, name="De otro", status=CertificationStatus.APPROVED)
    db.commit()

    r = http_client.get(f"{API}/projects/{proyecto.id}/team-certifications", headers=_auth(token_cliente))
    assert r.status_code == 200, r.text
    equipo = r.json()
    assert [m["user_id"] for m in equipo] == [tecnico.id]
    certs = equipo[0]["certifications"]
    assert [c["name"] for c in certs] == ["Fortinet NSE 4"]
    texto = r.text
    for prohibido in ("SECRETO-123", "nse4.pdf", "certifications/", "@ninjasec.local"):
        assert prohibido not in texto


def test_el_cliente_no_ve_el_equipo_de_un_proyecto_ajeno(http_client, db, org):
    _, token_cliente = _cliente_con_proyecto(db, org.id)
    ajeno, _ = _cliente_con_proyecto(db, org.id)
    r = http_client.get(f"{API}/projects/{ajeno.id}/team-certifications", headers=_auth(token_cliente))
    assert r.status_code == 404


def test_el_cliente_no_descarga_adjuntos(http_client, db, org, colaborador):
    tecnico, _ = colaborador
    _, token_cliente = _cliente_con_proyecto(db, org.id)
    cert = _certificacion(db, tecnico.id, status=CertificationStatus.APPROVED, file_key="certifications/1/x.pdf",
                          file_name="x.pdf")
    assert http_client.get(f"{API}/user-certifications/{cert.id}/file", headers=_auth(token_cliente)).status_code == 403


def test_un_proyecto_de_otra_organizacion_da_404_incluso_al_admin(http_client, db, admin_token):
    otra = Organization(name=f"Otra {uuid4().hex[:6]}", slug=f"otra-{uuid4().hex[:8]}")
    db.add(otra)
    db.commit()
    proyecto = Project(organization_id=otra.id, name="Ajeno")
    db.add(proyecto)
    db.commit()
    r = http_client.get(f"{API}/projects/{proyecto.id}/team-certifications", headers=_auth(admin_token))
    assert r.status_code == 404


# --- Migracion ----------------------------------------------------------------


def test_la_migracion_encadena_y_coincide_con_el_modelo():
    m = importlib.import_module("app.db.migrations.versions.20261129_01_certificados_adjuntos")
    assert m.revision == "20261129_01"
    columnas = UserCertification.__table__.c
    for nombre in m._COLUMNAS:
        assert nombre in columnas, nombre
