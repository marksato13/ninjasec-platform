"""El cliente no ve documentos en borrador ni el catalogo de otra organizacion.

Revision del portal del 2026-11-25 (Codex):
- `GET /project-docs` dejaba al cliente ver un documento en BORRADOR si estaba
  habilitado y marcado como visible para el cliente.
- `GET /services` con sesion de cliente mostraba servicios inactivos, privados y
  de otras organizaciones.
"""

from __future__ import annotations

from uuid import uuid4

from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.doc_type import DocType
from app.db.models.enums import ClientStatus, DocStatus, DocVisibility
from app.db.models.organization import Organization
from app.db.models.project import Project
from app.db.models.project_doc import ProjectDoc
from app.db.models.service import Service
from app.db.models.user import User
from tests.conftest import API
from tests.test_catalog_role_access import _client_token


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _proyecto_del_cliente(db, organization_id: int, token_email_suffix: str) -> Project:
    user = db.query(User).filter(User.email == f"portal-catalogos-{token_email_suffix}@ninjasec.local").one()
    perfil = db.query(ClientProfile).filter(ClientProfile.user_id == user.id).one()
    db.get(Client, perfil.client_id).commercial_status = ClientStatus.ACTIVE
    proyecto = Project(organization_id=organization_id, client_id=perfil.client_id, name="Proyecto del cliente")
    db.add(proyecto)
    db.commit()
    return proyecto


def _doc(db, project_id: int, estado: DocStatus) -> ProjectDoc:
    tipo = DocType(name=f"Informe {uuid4().hex[:8]}")
    db.add(tipo)
    db.flush()
    doc = ProjectDoc(
        project_id=project_id,
        doc_type_id=tipo.id,
        title=f"Doc {estado.value}",
        visibility=DocVisibility.CLIENT,
        status=estado,
        enabled=True,
    )
    db.add(doc)
    db.commit()
    return doc


def test_el_cliente_no_ve_borradores_en_la_lista_ni_en_la_descarga(db, http_client, seed_data):
    sufijo = f"docs-{uuid4().hex[:6]}"
    token = _client_token(db, http_client, seed_data["org"].id, sufijo)
    proyecto = _proyecto_del_cliente(db, seed_data["org"].id, sufijo)
    borrador = _doc(db, proyecto.id, DocStatus.DRAFT)
    publicado = _doc(db, proyecto.id, DocStatus.ACTIVE)

    r = http_client.get(f"{API}/project-docs", headers=_auth(token))
    assert r.status_code == 200, r.text
    ids = {d["id"] for d in r.json()}
    assert publicado.id in ids
    assert borrador.id not in ids

    r = http_client.get(f"{API}/project-docs/{borrador.id}/download", headers=_auth(token))
    assert r.status_code == 404


def test_el_cliente_ve_solo_el_catalogo_publico_y_activo_de_su_organizacion(db, http_client, seed_data):
    org = seed_data["org"].id
    otra = Organization(name=f"Otra {uuid4().hex[:8]}", slug=f"otra-{uuid4().hex[:8]}")
    db.add(otra)
    db.commit()

    def servicio(organization_id, **kw):
        s = uuid4().hex[:8]
        item = Service(organization_id=organization_id, title=f"S {s}", slug=f"s-{s}", **kw)
        db.add(item)
        db.commit()
        return item

    publico = servicio(org)
    inactivo = servicio(org, active=False)
    privado = servicio(org, is_public=False)
    ajeno = servicio(otra.id)

    token = _client_token(db, http_client, org, f"cat-{uuid4().hex[:6]}")
    r = http_client.get(f"{API}/services/", headers=_auth(token))
    assert r.status_code == 200, r.text
    ids = {d["id"] for d in r.json()}
    assert publico.id in ids
    assert not ids & {inactivo.id, privado.id, ajeno.id}
