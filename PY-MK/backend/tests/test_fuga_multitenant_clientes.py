"""Aislamiento multi-tenant en sedes, contactos y conexiones de topologia.

Tres fugas encontradas en la auditoria de base de datos del 2026-11-21. Las
tres compartian la misma causa: `client_sites`, `client_contacts` y
`devices` **no llevan `organization_id`**, asi que el tenant hay que
derivarlo por su cliente o su integracion -- y en estos tres sitios no se
derivaba.

AGENTS.md ya fijaba la regla ("datos de otra organizacion devuelven 404 para
no confirmar su existencia") y el patron correcto ya existia en
`clients/routers/client_services.py`. Simplemente no se habia aplicado aqui.
"""

import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models.client import Client
from app.db.models.client_contact import ClientContact
from app.db.models.client_site import ClientSite
from app.db.models.enums import RoleCode, SiteStatus, UserStatus
from app.db.models.organization import Organization
from app.db.models.role import Role
from app.db.models.user import User
from tests.conftest import API


@pytest.fixture
def otra_org(db: Session):
    """Una organizacion completamente ajena, con su cliente, sede y contacto.

    Nada de esto debe ser visible ni alcanzable desde la organizacion del
    usuario de pruebas.

    Los identificadores llevan sufijo aleatorio porque la base de pruebas
    persiste entre tests de la misma sesion: sin eso, el segundo test que
    pida la fixture choca con el slug y el email del primero.
    """
    sufijo = uuid4().hex[:8]
    org = Organization(name=f"Ajena SAC {sufijo}", slug=f"ajena-sac-{sufijo}")
    db.add(org)
    db.flush()

    rol = db.query(Role).filter(Role.code == RoleCode.ADMIN.value).first()
    if not rol:
        rol = Role(code=RoleCode.ADMIN.value, name="Admin")
        db.add(rol)
        db.flush()

    admin_ajeno = User(
        organization_id=org.id,
        role_id=rol.id,
        role_code=RoleCode.ADMIN,
        full_name="Admin Ajeno",
        email=f"admin@{org.slug}.test",
        password_hash=hash_password("no-importa"),
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    cliente = Client(organization_id=org.id, company_name="Cliente Ajeno")
    db.add_all([admin_ajeno, cliente])
    db.flush()

    sede = ClientSite(
        client_id=cliente.id,
        name="Sede Ajena",
        address="Calle Falsa 123",
        status=SiteStatus.ACTIVE,
    )
    contacto = ClientContact(
        client_id=cliente.id,
        name="Persona Ajena",
        email=f"persona@{org.slug}.test",
        phone="999000111",
    )
    db.add_all([sede, contacto])
    db.commit()

    return {"org": org, "cliente": cliente, "sede": sede, "contacto": contacto}


# ---------------------------------------------------------------------------
# Sedes
# ---------------------------------------------------------------------------


def test_el_listado_de_sedes_no_incluye_las_de_otra_organizacion(
    http_client, admin_token, otra_org
):
    r = http_client.get(
        f"{API}/client-sites/", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r.status_code == 200

    ids = {s["id"] for s in r.json()}
    assert otra_org["sede"].id not in ids, (
        "El listado de sedes expone la sede de otra organizacion"
    )


def test_no_se_puede_editar_una_sede_ajena(http_client, admin_token, otra_org):
    r = http_client.put(
        f"{API}/client-sites/{otra_org['sede'].id}",
        json={"name": "Secuestrada"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 404, (
        f"Editar una sede ajena devolvio {r.status_code}. Debe ser 404: "
        "un 403 confirmaria que existe."
    )


def test_no_se_puede_borrar_una_sede_ajena(http_client, admin_token, otra_org, db):
    r = http_client.delete(
        f"{API}/client-sites/{otra_org['sede'].id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 404

    # Y sigue existiendo: no basta con que responda 404 si ya la borro.
    assert db.get(ClientSite, otra_org["sede"].id) is not None, (
        "La sede ajena fue borrada fisicamente"
    )


def test_no_se_puede_crear_una_sede_dentro_de_un_cliente_ajeno(
    http_client, admin_token, otra_org
):
    r = http_client.post(
        f"{API}/client-sites/",
        json={
            "client_id": otra_org["cliente"].id,
            "name": "Sede infiltrada",
            "address": "x",
            "status": "active",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 404, (
        f"Se creo una sede dentro del cliente de otra organizacion ({r.status_code})"
    )


# ---------------------------------------------------------------------------
# Contactos -- fuga de datos personales
# ---------------------------------------------------------------------------


def test_el_listado_de_contactos_no_filtra_datos_personales_ajenos(
    http_client, admin_token, otra_org
):
    """El peor de los tres: nombre, correo y telefono de personas reales."""
    r = http_client.get(
        f"{API}/client-contacts/", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r.status_code == 200

    cuerpo = r.text
    assert otra_org["contacto"].email not in cuerpo, (
        "El listado expone el correo de un contacto de otra organizacion"
    )
    assert "999000111" not in cuerpo, (
        "El listado expone el telefono de un contacto de otra organizacion"
    )

    ids = {c["id"] for c in r.json()}
    assert otra_org["contacto"].id not in ids


def test_no_se_puede_editar_un_contacto_ajeno(http_client, admin_token, otra_org):
    r = http_client.put(
        f"{API}/client-contacts/{otra_org['contacto'].id}",
        json={"name": "Secuestrado"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 404


def test_no_se_puede_borrar_un_contacto_ajeno(http_client, admin_token, otra_org, db):
    r = http_client.delete(
        f"{API}/client-contacts/{otra_org['contacto'].id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 404
    assert db.get(ClientContact, otra_org["contacto"].id) is not None


def test_no_se_puede_crear_un_contacto_en_un_cliente_ajeno(
    http_client, admin_token, otra_org
):
    r = http_client.post(
        f"{API}/client-contacts/",
        json={
            "client_id": otra_org["cliente"].id,
            "name": "Infiltrado",
            "email": "infiltrado@ejemplo.com",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# El filtro por client_id no puede ser una puerta trasera
# ---------------------------------------------------------------------------


def test_pasar_el_client_id_ajeno_en_la_query_no_devuelve_nada(
    http_client, admin_token, otra_org
):
    """El parametro `client_id` acota, nunca amplia.

    Sin el filtro de organizacion en la consulta base, pasar el id del
    cliente ajeno habria devuelto justo sus datos -- el camino mas directo
    para explotar la fuga.
    """
    ajeno = otra_org["cliente"].id
    cabeceras = {"Authorization": f"Bearer {admin_token}"}

    r_sedes = http_client.get(f"{API}/client-sites/?client_id={ajeno}", headers=cabeceras)
    assert r_sedes.status_code == 200
    assert r_sedes.json() == []

    r_contactos = http_client.get(
        f"{API}/client-contacts/?client_id={ajeno}", headers=cabeceras
    )
    assert r_contactos.status_code == 200
    assert r_contactos.json() == []
