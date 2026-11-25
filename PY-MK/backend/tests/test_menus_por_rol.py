"""Menus editables por rol.

Lo que se comprueba, y por que:

- Sin ediciones, cada rol ve lo mismo que veia con el menu escrito en el
  codigo. Es el requisito que impide que esta funcion cambie nada por si sola.
- Solo el super_admin edita.
- El editor NO deja mostrar a un rol una pantalla que el backend no le deja
  usar, ni ocultar lo que dejaria a alguien sin forma de entrar.
- Un lote invalido no aplica NADA, ni siquiera la parte valida.
- Cada organizacion edita su menu sin tocar el de otra.
- Una capsula apagada manda sobre lo que diga la configuracion.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.core.navegacion import OPCIONES, SUPERFICIES, opciones_de
from app.core.security import hash_password
from app.db.models.enums import RoleCode, UserStatus
from app.db.models.nav_visibility import NavVisibility
from app.db.models.organization import Organization
from app.db.models.role import Role
from app.db.models.user import User

API = "/api/v1/navigation"
LOGIN = "/api/v1/auth/login"
CLAVE = "menus-password-123"


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _rol(db, code: RoleCode) -> Role:
    rol = db.scalar(select(Role).where(Role.code == code.value))
    if rol is None:
        rol = Role(code=code.value, name=code.value)
        db.add(rol)
        db.flush()
    return rol


def _organizacion_del_sitio(db) -> Organization:
    """La misma que usara el endpoint publico: la interna, o la primera."""
    org = db.scalar(select(Organization).where(Organization.slug == "ninjasec-internal"))
    return org or db.scalar(select(Organization).order_by(Organization.id))


def _usuario(db, org: Organization, code: RoleCode, email: str) -> None:
    if db.scalar(select(User).where(User.email == email)):
        return
    db.add(User(
        organization_id=org.id, role_id=_rol(db, code).id, full_name=f"Menus {code.value}",
        email=email, password_hash=hash_password(CLAVE), role_code=code,
        status=UserStatus.ACTIVE, is_active=True,
    ))
    db.commit()


def _token(http_client, email: str) -> str:
    r = http_client.post(LOGIN, json={"email": email, "password": CLAVE})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(autouse=True)
def tabla_limpia(db):
    """La base de pruebas dura toda la sesion: cada prueba parte y termina vacia."""
    db.query(NavVisibility).delete()
    db.commit()
    yield
    db.query(NavVisibility).delete()
    db.commit()


@pytest.fixture
def org(db, seed_data):
    return _organizacion_del_sitio(db)


@pytest.fixture
def super_token(db, http_client, org):
    _usuario(db, org, RoleCode.SUPER_ADMIN, "menus-super@ninjasec.local")
    return _token(http_client, "menus-super@ninjasec.local")


@pytest.fixture
def admin_tok(db, http_client, org):
    _usuario(db, org, RoleCode.ADMIN, "menus-admin@ninjasec.local")
    return _token(http_client, "menus-admin@ninjasec.local")


@pytest.fixture
def collab_tok(db, http_client, org):
    _usuario(db, org, RoleCode.COLLABORATOR, "menus-collab@ninjasec.local")
    return _token(http_client, "menus-collab@ninjasec.local")


@pytest.fixture
def client_tok(db, http_client, org):
    _usuario(db, org, RoleCode.CLIENT, "menus-client@ninjasec.local")
    return _token(http_client, "menus-client@ninjasec.local")


def _put(http_client, token, *cambios):
    return http_client.put(f"{API}/config", headers=_auth(token), json={"cambios": list(cambios)})


def _cambio(superficie, clave, audiencia, visible):
    return {"superficie": superficie, "clave": clave, "audiencia": audiencia, "visible": visible}


# ---------------------------------------------------------------------------
# Sin ediciones: nada cambia
# ---------------------------------------------------------------------------


def test_sin_ediciones_el_menu_publico_muestra_todo(http_client, org):
    r = http_client.get(f"{API}/public")
    assert r.status_code == 200
    assert r.json()["visibles"] == [o.clave for o in opciones_de("public")]


def test_sin_ediciones_el_super_admin_ve_el_panel_completo(http_client, super_token):
    visibles = http_client.get(f"{API}/me", headers=_auth(super_token)).json()["staff"]
    assert "/dashboard/audit" in visibles
    assert "/dashboard/settings" in visibles


def test_sin_ediciones_el_admin_no_ve_auditoria(http_client, admin_tok):
    visibles = http_client.get(f"{API}/me", headers=_auth(admin_tok)).json()["staff"]
    assert "/dashboard/audit" not in visibles
    assert "/dashboard/users" in visibles


def test_sin_ediciones_el_colaborador_ve_lo_que_veia(http_client, collab_tok):
    datos = http_client.get(f"{API}/me", headers=_auth(collab_tok)).json()
    visibles = datos["staff"]
    for oculta in ("/dashboard", "/dashboard/leads", "/dashboard/services",
                   "/dashboard/users", "/dashboard/applications", "/dashboard/reports",
                   "/dashboard/approvals", "/dashboard/audit", "/dashboard/settings"):
        assert oculta not in visibles, oculta
    for propia in ("/dashboard/projects", "/dashboard/clients", "/dashboard/collaborators"):
        assert propia in visibles, propia
    # y el portal de colaborador
    assert set(datos["portal"]) == {"/portal", "/portal/profile", "/portal/applications",
                                    "/portal/tasks", "/portal/resources", "/portal/work-windows"}


def test_sin_ediciones_el_cliente_solo_tiene_portal(http_client, client_tok):
    datos = http_client.get(f"{API}/me", headers=_auth(client_tok)).json()
    assert datos["staff"] is None
    assert set(datos["portal"]) == {"/portal", "/portal/projects", "/portal/inventory", "/portal/documents",
                                    "/portal/tickets", "/portal/services", "/portal/profile", "/portal/work-windows"}


def test_la_tabla_esta_vacia_si_nadie_edita(db):
    assert db.scalar(select(func.count()).select_from(NavVisibility)) == 0


# ---------------------------------------------------------------------------
# Quien edita
# ---------------------------------------------------------------------------


def test_solo_el_super_admin_lee_y_edita(http_client, admin_tok, collab_tok, client_tok):
    for tok in (admin_tok, collab_tok, client_tok):
        assert http_client.get(f"{API}/config", headers=_auth(tok)).status_code == 403
        assert _put(http_client, tok, _cambio("public", "/nosotros", "visitor", False)).status_code == 403


def test_sin_sesion_no_se_edita(http_client):
    assert http_client.get(f"{API}/config").status_code == 401
    assert http_client.put(f"{API}/config", json={"cambios": []}).status_code in (401, 422)


def test_el_menu_publico_se_lee_sin_sesion(http_client, org):
    assert http_client.get(f"{API}/public").status_code == 200


# ---------------------------------------------------------------------------
# Editar
# ---------------------------------------------------------------------------


def test_ocultar_una_opcion_publica(http_client, super_token):
    r = _put(http_client, super_token, _cambio("public", "/nosotros", "visitor", False))
    assert r.status_code == 200, r.text
    visibles = http_client.get(f"{API}/public").json()["visibles"]
    assert "/nosotros" not in visibles
    assert "/servicios" in visibles


def test_ocultar_solo_a_un_rol_no_toca_a_los_demas(http_client, super_token, admin_tok, collab_tok):
    r = _put(http_client, super_token, _cambio("staff", "/dashboard/projects", "collaborator", False))
    assert r.status_code == 200, r.text
    assert "/dashboard/projects" not in http_client.get(f"{API}/me", headers=_auth(collab_tok)).json()["staff"]
    assert "/dashboard/projects" in http_client.get(f"{API}/me", headers=_auth(admin_tok)).json()["staff"]


def test_volver_a_mostrar_borra_la_excepcion(db, http_client, super_token):
    _put(http_client, super_token, _cambio("staff", "/dashboard/risks", "admin", False))
    assert db.scalar(select(func.count()).select_from(NavVisibility)) == 1
    _put(http_client, super_token, _cambio("staff", "/dashboard/risks", "admin", True))
    # Es el valor por defecto: no se guarda, se borra.
    assert db.scalar(select(func.count()).select_from(NavVisibility)) == 0


def test_la_matriz_refleja_lo_editado(http_client, super_token):
    _put(http_client, super_token, _cambio("portal", "/portal/services", "client", False))
    matriz = http_client.get(f"{API}/config", headers=_auth(super_token)).json()["superficies"]
    fila = next(o for o in matriz["portal"]["opciones"] if o["clave"] == "/portal/services")
    assert fila["visible"] == {"client": False}
    assert set(matriz) == set(SUPERFICIES)


def test_la_edicion_queda_en_la_auditoria(db, http_client, super_token):
    from app.db.models.audit_log import AuditLog

    antes = db.scalar(select(func.count()).select_from(AuditLog).where(
        AuditLog.entity_type == "nav_visibility"))
    _put(http_client, super_token, _cambio("public", "/contacto", "visitor", False))
    despues = db.scalar(select(func.count()).select_from(AuditLog).where(
        AuditLog.entity_type == "nav_visibility"))
    assert despues == antes + 1


# ---------------------------------------------------------------------------
# Lo que el editor se niega a hacer
# ---------------------------------------------------------------------------


def test_no_se_muestra_a_un_rol_lo_que_el_backend_no_le_deja_usar(http_client, super_token):
    # Leads es solo de admin: un colaborador veria el enlace y recibiria un 403.
    r = _put(http_client, super_token, _cambio("staff", "/dashboard/leads", "collaborator", True))
    assert r.status_code == 422
    assert "no esta disponible" in r.json()["detail"]


def test_no_se_puede_ocultar_el_login(http_client, super_token):
    r = _put(http_client, super_token, _cambio("public", "/login", "visitor", False))
    assert r.status_code == 422


def test_el_super_admin_no_puede_ocultarse_la_configuracion(http_client, super_token):
    r = _put(http_client, super_token, _cambio("staff", "/dashboard/settings", "super_admin", False))
    assert r.status_code == 422


def test_opcion_o_audiencia_inexistente(http_client, super_token):
    assert _put(http_client, super_token, _cambio("public", "/no-existe", "visitor", False)).status_code == 422
    assert _put(http_client, super_token, _cambio("public", "/nosotros", "client", False)).status_code == 422
    assert _put(http_client, super_token, _cambio("otra", "/nosotros", "visitor", False)).status_code == 422


def test_un_lote_invalido_no_aplica_nada(db, http_client, super_token):
    r = _put(
        http_client, super_token,
        _cambio("public", "/nosotros", "visitor", False),      # valido
        _cambio("public", "/login", "visitor", False),         # invalido
    )
    assert r.status_code == 422
    assert db.scalar(select(func.count()).select_from(NavVisibility)) == 0
    assert "/nosotros" in http_client.get(f"{API}/public").json()["visibles"]


# ---------------------------------------------------------------------------
# Aislamiento entre organizaciones
# ---------------------------------------------------------------------------


def test_otra_organizacion_no_ve_ni_pisa_mis_ediciones(db, http_client, super_token):
    otra = Organization(name="Menus Otra Org", slug="menus-otra-org")
    db.add(otra)
    db.flush()
    _usuario(db, otra, RoleCode.SUPER_ADMIN, "menus-super-otra@ninjasec.local")
    _usuario(db, otra, RoleCode.COLLABORATOR, "menus-collab-otra@ninjasec.local")

    # La organizacion A oculta Proyectos a sus colaboradores.
    _put(http_client, super_token, _cambio("staff", "/dashboard/projects", "collaborator", False))

    # La organizacion B no lo nota...
    tok_colab_b = _token(http_client, "menus-collab-otra@ninjasec.local")
    assert "/dashboard/projects" in http_client.get(f"{API}/me", headers=_auth(tok_colab_b)).json()["staff"]

    # ...y su matriz no trae la edicion de A.
    tok_super_b = _token(http_client, "menus-super-otra@ninjasec.local")
    matriz = http_client.get(f"{API}/config", headers=_auth(tok_super_b)).json()["superficies"]
    fila = next(o for o in matriz["staff"]["opciones"] if o["clave"] == "/dashboard/projects")
    assert fila["visible"]["collaborator"] is True

    # Y lo que B edite no llega a A.
    _put(http_client, tok_super_b, _cambio("staff", "/dashboard/devices", "collaborator", False))
    filas_a = db.scalars(select(NavVisibility).where(NavVisibility.organization_id == _organizacion_del_sitio(db).id)).all()
    assert {f.item_key for f in filas_a} == {"/dashboard/projects"}


# ---------------------------------------------------------------------------
# Capsulas
# ---------------------------------------------------------------------------


def test_una_capsula_apagada_manda_sobre_la_configuracion(http_client, collab_tok, monkeypatch):
    from app.core.config import settings

    # En las pruebas todas las capsulas estan encendidas.
    assert "/dashboard/integrations" in http_client.get(f"{API}/me", headers=_auth(collab_tok)).json()["staff"]

    monkeypatch.setattr(settings, "capsulas_activas", "")
    visibles = http_client.get(f"{API}/me", headers=_auth(collab_tok)).json()["staff"]
    for ruta in ("/dashboard/integrations", "/dashboard/hardening", "/dashboard/soc-report"):
        assert ruta not in visibles, ruta


def test_cada_opcion_de_telemetria_declara_su_capsula():
    """Si se anade una pantalla de telemetria, tiene que quedar atada a la capsula."""
    from app.core.features import CAPSULAS

    asociadas = {o.clave for o in OPCIONES if o.capsula == "telemetria"}
    registro = {ruta for c in CAPSULAS.values() for ruta in getattr(c, "rutas_ui", ())}
    assert registro <= asociadas, f"Faltan en navegacion.py: {registro - asociadas}"
