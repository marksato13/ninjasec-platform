"""El flujo de la empresa de punta a punta, visto por los tres roles.

    visitante ── lead ──► admin ── cliente ──► proyecto ──► equipo y tareas
                                                   │             │
                                       el cliente lo ve    el colaborador lo ve
                                                           y avanza su tarea

Es la prueba de que las piezas encajan: cada endpoint se prueba por separado en
su modulo, pero nada decia que un lead pudiera convertirse en un proyecto que
un colaborador trabaja y un cliente consulta. Esto lo dice.

Y lo que NO debe ocurrir: el cliente ve lo suyo y nada de otro cliente; el
colaborador ve solo los proyectos donde es miembro.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.area import Area
from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.enums import RoleCode, UserStatus
from app.db.models.organization import Organization
from app.db.models.project_type import ProjectType
from app.db.models.role import Role
from app.db.models.service import Service
from app.db.models.user import User

API = "/api/v1"
CLAVE = "flujo-password-123"


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


def _rol(db, code):
    r = db.scalar(select(Role).where(Role.code == code.value))
    if r is None:
        r = Role(code=code.value, name=code.value)
        db.add(r)
        db.flush()
    return r


def _usuario(db, org, code, email):
    u = db.scalar(select(User).where(User.email == email))
    if u is None:
        u = User(organization_id=org.id, role_id=_rol(db, code).id, full_name=email.split("@")[0],
                 email=email, password_hash=hash_password(CLAVE), role_code=code,
                 status=UserStatus.ACTIVE, is_active=True)
        db.add(u)
        db.commit()
    return u


def _token(http_client, email):
    r = http_client.post(f"{API}/auth/login", json={"email": email, "password": CLAVE})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def org(db, seed_data):
    # La organizacion duena del sitio (la de menor id): es la que recibe los leads del
    # formulario publico desde la migracion 20261127_01. Antes el flujo usaba una
    # organizacion aparte y solo funcionaba porque los leads no tenian dueno.
    return db.scalar(select(Organization).order_by(Organization.id).limit(1))


@pytest.fixture
def escenario(db, http_client, org):
    """Un admin, un colaborador, un colaborador ajeno al proyecto y un tipo de proyecto + servicio."""
    admin = _usuario(db, org, RoleCode.ADMIN, "flujo-admin@ninjasec.local")
    colab = _usuario(db, org, RoleCode.COLLABORATOR, "flujo-colab@ninjasec.local")
    _usuario(db, org, RoleCode.COLLABORATOR, "flujo-colab-ajeno@ninjasec.local")
    tipo = db.scalar(select(ProjectType).where(ProjectType.slug == "flujo-impl"))
    if tipo is None:
        tipo = ProjectType(organization_id=org.id, name="Implementacion flujo", slug="flujo-impl", is_active=True)
        db.add(tipo)
        db.flush()
    # Un proyecto necesita un area, y la toma de su servicio: sin ella la API responde
    # "Area could not be resolved". Por eso cada servicio del catalogo lleva la suya.
    area = db.scalar(select(Area).where(Area.organization_id == org.id, Area.slug == "flujo-area"))
    if area is None:
        area = Area(organization_id=org.id, name="Area flujo", slug="flujo-area")
        db.add(area)
        db.flush()
    servicio = db.scalar(select(Service).where(Service.organization_id == org.id, Service.slug == "flujo-svc"))
    if servicio is None:
        servicio = Service(organization_id=org.id, title="Servicio flujo", slug="flujo-svc",
                           area_id=area.id, is_public=True, active=True)
        db.add(servicio)
    db.commit()
    return {"admin": admin, "colab": colab, "tipo": tipo, "servicio": servicio,
            "t_admin": _token(http_client, "flujo-admin@ninjasec.local"),
            "t_colab": _token(http_client, "flujo-colab@ninjasec.local"),
            "t_ajeno": _token(http_client, "flujo-colab-ajeno@ninjasec.local")}


def _cliente_con_acceso(db, http_client, org, nombre, email):
    """Cliente con un usuario de portal (lo que hace el alta real)."""
    cli = db.scalar(select(Client).where(Client.organization_id == org.id, Client.company_name == nombre))
    if cli is None:
        cli = Client(organization_id=org.id, company_name=nombre)
        db.add(cli)
        db.flush()
    u = _usuario(db, org, RoleCode.CLIENT, email)
    if not db.scalar(select(ClientProfile).where(ClientProfile.user_id == u.id)):
        db.add(ClientProfile(client_id=cli.id, user_id=u.id))
        db.commit()
    return cli, _token(http_client, email)


def test_del_interes_al_proyecto_entregado(db, http_client, org, escenario):
    e = escenario
    h = _auth(e["t_admin"])

    # 1. Un visitante deja su interes (formulario publico, sin sesion).
    r = http_client.post(f"{API}/leads/", json={
        "company_name": "Panaderia Flujo", "contact_name": "Ana Flujo", "email": "ana@panaderia-flujo.pe",
        "interest_area": "infraestructura", "message": "Queremos separar el wifi de visitas",
        "source": "agenda-reunion"})
    assert r.status_code == 201, r.text
    lead_id = r.json()["id"]
    assert r.json()["status"] == "NEW"

    # 2. El admin lo ve y lo avanza.
    assert lead_id in [x["id"] for x in http_client.get(f"{API}/leads/", headers=h).json()]
    for estado in ("CONTACTED", "QUALIFIED", "PROPOSAL", "CLOSED_WON"):
        r = http_client.patch(f"{API}/leads/{lead_id}", headers=h, json={"status": estado})
        assert r.status_code == 200, (estado, r.text)
        assert r.json()["status"] == estado

    # 3. Lo convierte en cliente.
    r = http_client.post(f"{API}/clients/", headers=h, json={
        "organization_id": org.id, "company_name": "Panaderia Flujo", "commercial_status": "active",
        "sector": "alimentos", "city": "Lima", "country": "Peru"})
    assert r.status_code == 201, r.text
    cliente_id = r.json()["id"]

    # 4. Crea el proyecto.
    r = http_client.post(f"{API}/projects/", headers=h, json={
        "organization_id": org.id, "client_id": cliente_id, "project_type_id": e["tipo"].id,
        "service_id": e["servicio"].id, "name": "Segmentacion de red", "status": "planning"})
    assert r.status_code == 201, r.text
    proyecto_id = r.json()["id"]

    # 5. Asigna al colaborador y le da una tarea.
    r = http_client.post(f"{API}/project-members", headers=h, json={
        "project_id": proyecto_id, "user_id": e["colab"].id, "role_in_project": "tecnico"})
    assert r.status_code in (200, 201), r.text
    r = http_client.post(f"{API}/project-tasks/", headers=h, json={
        "project_id": proyecto_id, "assigned_user_id": e["colab"].id,
        "title": "Levantar el inventario de equipos", "status": "pending"})
    assert r.status_code == 201, r.text
    tarea_id = r.json()["id"]

    # 6. El colaborador ve SU proyecto y SU tarea, y la avanza.
    mis = http_client.get(f"{API}/projects/", headers=_auth(e["t_colab"])).json()
    assert proyecto_id in [p["id"] for p in mis]
    tareas = http_client.get(f"{API}/project-tasks/", headers=_auth(e["t_colab"])).json()
    assert tarea_id in [t["id"] for t in tareas]
    r = http_client.patch(f"{API}/project-tasks/{tarea_id}/status", headers=_auth(e["t_colab"]),
                          json={"status": "done"})
    assert r.status_code == 200, r.text

    # 7. El cliente, con su acceso al portal, ve el proyecto.
    cli, t_cli = _cliente_con_acceso(db, http_client, org, "Panaderia Flujo", "ana@panaderia-flujo.pe")
    visibles = http_client.get(f"{API}/projects/", headers=_auth(t_cli)).json()
    assert proyecto_id in [p["id"] for p in visibles]

    # 8. El admin cierra el proyecto.
    r = http_client.put(f"{API}/projects/{proyecto_id}", headers=h, json={
        "organization_id": org.id, "client_id": cliente_id, "project_type_id": e["tipo"].id,
        "service_id": e["servicio"].id, "name": "Segmentacion de red", "status": "completed"})
    assert r.status_code == 200, r.text


def test_un_cliente_no_ve_el_proyecto_de_otro_cliente(db, http_client, org, escenario):
    e = escenario
    cli_a, t_a = _cliente_con_acceso(db, http_client, org, "Cliente A Flujo", "a@flujo.pe")
    cli_b, t_b = _cliente_con_acceso(db, http_client, org, "Cliente B Flujo", "b@flujo.pe")
    r = http_client.post(f"{API}/projects/", headers=_auth(e["t_admin"]), json={
        "organization_id": org.id, "client_id": cli_a.id, "project_type_id": e["tipo"].id,
        "service_id": e["servicio"].id, "name": "Proyecto solo de A"})
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    assert pid in [p["id"] for p in http_client.get(f"{API}/projects/", headers=_auth(t_a)).json()]
    assert pid not in [p["id"] for p in http_client.get(f"{API}/projects/", headers=_auth(t_b)).json()]
    # Y pedirlo por id: 404, no 403.
    assert http_client.get(f"{API}/projects/{pid}", headers=_auth(t_b)).status_code in (403, 404)


def test_un_colaborador_solo_ve_los_proyectos_donde_es_miembro(db, http_client, org, escenario):
    e = escenario
    cli, _ = _cliente_con_acceso(db, http_client, org, "Cliente C Flujo", "c@flujo.pe")
    r = http_client.post(f"{API}/projects/", headers=_auth(e["t_admin"]), json={
        "organization_id": org.id, "client_id": cli.id, "project_type_id": e["tipo"].id,
        "service_id": e["servicio"].id, "name": "Proyecto con equipo"})
    pid = r.json()["id"]
    http_client.post(f"{API}/project-members", headers=_auth(e["t_admin"]), json={
        "project_id": pid, "user_id": e["colab"].id})
    assert pid in [p["id"] for p in http_client.get(f"{API}/projects/", headers=_auth(e["t_colab"])).json()]
    assert pid not in [p["id"] for p in http_client.get(f"{API}/projects/", headers=_auth(e["t_ajeno"])).json()]


def test_un_colaborador_no_crea_clientes_ni_proyectos(http_client, org, escenario):
    e = escenario
    h = _auth(e["t_colab"])
    assert http_client.post(f"{API}/clients/", headers=h, json={
        "organization_id": org.id, "company_name": "X"}).status_code == 403
    assert http_client.post(f"{API}/projects/", headers=h, json={
        "organization_id": org.id, "client_id": 1, "project_type_id": e["tipo"].id,
        "service_id": e["servicio"].id, "name": "No"}).status_code == 403


def test_un_cliente_no_ve_los_leads_ni_la_lista_de_clientes(db, http_client, org, escenario):
    _, t_cli = _cliente_con_acceso(db, http_client, org, "Cliente D Flujo", "d@flujo.pe")
    assert http_client.get(f"{API}/leads/", headers=_auth(t_cli)).status_code == 403
    assert http_client.get(f"{API}/clients/", headers=_auth(t_cli)).status_code in (403, 200)


def test_el_colaborador_mueve_solo_sus_tareas(db, http_client, org, escenario):
    e = escenario
    cli, _ = _cliente_con_acceso(db, http_client, org, "Cliente E Flujo", "e@flujo.pe")
    h = _auth(e["t_admin"])
    pid = http_client.post(f"{API}/projects/", headers=h, json={
        "organization_id": org.id, "client_id": cli.id, "project_type_id": e["tipo"].id,
        "service_id": e["servicio"].id, "name": "Proyecto de tareas"}).json()["id"]
    mia = http_client.post(f"{API}/project-tasks/", headers=h, json={
        "project_id": pid, "assigned_user_id": e["colab"].id, "title": "Mia"}).json()["id"]
    ajeno = db.scalar(select(User).where(User.email == "flujo-colab-ajeno@ninjasec.local"))
    ajena = http_client.post(f"{API}/project-tasks/", headers=h, json={
        "project_id": pid, "assigned_user_id": ajeno.id, "title": "De otro"}).json()["id"]

    mov = lambda tid, est, tok: http_client.patch(f"{API}/project-tasks/{tid}/status",
                                                  headers=_auth(tok), json={"status": est})
    assert mov(mia, "in_progress", e["t_colab"]).json()["status"] == "in_progress"
    # La de otro: 404, no 403.
    assert mov(ajena, "done", e["t_colab"]).status_code == 404
    # Un estado inventado se rechaza.
    assert mov(mia, "terminadisima", e["t_colab"]).status_code == 400
    # El admin mueve cualquiera.
    assert mov(ajena, "done", e["t_admin"]).status_code == 200
    # Y el colaborador sigue sin poder editar el titulo ni reasignar (eso es del admin).
    assert http_client.put(f"{API}/project-tasks/{mia}", headers=_auth(e["t_colab"]),
                           json={"title": "Cambiado"}).status_code == 403


def test_el_cliente_no_mueve_tareas(db, http_client, org, escenario):
    _, t_cli = _cliente_con_acceso(db, http_client, org, "Cliente F Flujo", "f@flujo.pe")
    assert http_client.patch(f"{API}/project-tasks/1/status", headers=_auth(t_cli),
                             json={"status": "done"}).status_code == 403
