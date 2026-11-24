"""Seguimiento de proyectos: lo que ve el cliente, lo que hace el especialista y lo que NO se filtra.

Lo que mas importa aqui es la frontera: un cliente ve SU proyecto, solo lo que se marco
visible, sin correos del equipo y sin IP de los equipos. Todo lo demas es comodidad.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.core import fases
from app.core.security import hash_password
from app.db.models.area import Area
from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.client_site import ClientSite
from app.db.models.device import Device
from app.db.models.enums import RoleCode, UserStatus
from app.db.models.organization import Organization
from app.db.models.project_tracking import ProjectDevice, ProjectUpdate
from app.db.models.project_type import ProjectType
from app.db.models.role import Role
from app.db.models.service import Service
from app.db.models.user import User

API = "/api/v1"
CLAVE = "seguimiento-password-123"


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
        u = User(organization_id=org.id, role_id=_rol(db, code).id, full_name=email.split("@")[0].title(),
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
    o = db.scalar(select(Organization).where(Organization.slug == "seg-org"))
    if o is None:
        o = Organization(name="Seg Org", slug="seg-org")
        db.add(o)
        db.commit()
    return o


@pytest.fixture
def mundo(db, http_client, org):
    """Admin, dos colaboradores (uno miembro), dos clientes con su acceso, un proyecto de cada
    linea y un equipo con IP en la sede del cliente A."""
    admin = _usuario(db, org, RoleCode.ADMIN, "seg-admin@ninjasec.local")
    miembro = _usuario(db, org, RoleCode.COLLABORATOR, "seg-miembro@ninjasec.local")
    _usuario(db, org, RoleCode.COLLABORATOR, "seg-ajeno@ninjasec.local")
    tipo = db.scalar(select(ProjectType).where(ProjectType.slug == "seg-tipo"))
    if tipo is None:
        tipo = ProjectType(organization_id=org.id, name="Seg tipo", slug="seg-tipo", is_active=True)
        db.add(tipo)
    area = db.scalar(select(Area).where(Area.organization_id == org.id, Area.slug == "seg-area"))
    if area is None:
        area = Area(organization_id=org.id, name="Seg area", slug="seg-area")
        db.add(area)
        db.flush()
    svc = {}
    for slug, cat in (("seg-infra", "infraestructura"), ("seg-dev", "desarrollo")):
        s = db.scalar(select(Service).where(Service.organization_id == org.id, Service.slug == slug))
        if s is None:
            s = Service(organization_id=org.id, title=slug, slug=slug, category=cat, area_id=area.id,
                        is_public=True, active=True)
            db.add(s)
        svc[slug] = s
    db.commit()

    def cliente(nombre, correo):
        c = db.scalar(select(Client).where(Client.organization_id == org.id, Client.company_name == nombre))
        if c is None:
            c = Client(organization_id=org.id, company_name=nombre)
            db.add(c)
            db.flush()
        u = _usuario(db, org, RoleCode.CLIENT, correo)
        if not db.scalar(select(ClientProfile).where(ClientProfile.user_id == u.id)):
            db.add(ClientProfile(client_id=c.id, user_id=u.id))
        db.commit()
        return c

    a, b = cliente("Seg Cliente A", "seg-a@cliente.pe"), cliente("Seg Cliente B", "seg-b@cliente.pe")
    h = _auth(_token(http_client, "seg-admin@ninjasec.local"))

    def proyecto(cli, nombre, servicio):
        r = http_client.post(f"{API}/projects/", headers=h, json={
            "organization_id": org.id, "client_id": cli.id, "project_type_id": tipo.id,
            "service_id": servicio.id, "name": nombre})
        assert r.status_code == 201, r.text
        return r.json()["id"]

    p_infra = proyecto(a, "Red de A", svc["seg-infra"])
    p_dev = proyecto(a, "App de A", svc["seg-dev"])
    p_b = proyecto(b, "Red de B", svc["seg-infra"])
    http_client.post(f"{API}/project-members", headers=h, json={
        "project_id": p_infra, "user_id": miembro.id, "role_in_project": "Redes"})

    sede = db.scalar(select(ClientSite).where(ClientSite.client_id == a.id))
    if sede is None:
        sede = ClientSite(client_id=a.id, name="Sede A")
        db.add(sede)
        db.flush()
    eq = db.scalar(select(Device).where(Device.hostname == "fw-seg-a"))
    if eq is None:
        eq = Device(hostname="fw-seg-a", vendor="Fortinet", model="60F", device_type="firewall",
                    ip_address="10.99.99.1", status="online", site_id=sede.id)
        db.add(eq)
    db.commit()
    return {"admin": admin, "miembro": miembro, "a": a, "b": b, "equipo": eq, "sede": sede,
            "p_infra": p_infra, "p_dev": p_dev, "p_b": p_b, "h": h,
            "t_miembro": _token(http_client, "seg-miembro@ninjasec.local"),
            "t_ajeno": _token(http_client, "seg-ajeno@ninjasec.local"),
            "t_a": _token(http_client, "seg-a@cliente.pe"),
            "t_b": _token(http_client, "seg-b@cliente.pe")}


@pytest.fixture(autouse=True)
def limpio(db):
    yield
    db.query(ProjectUpdate).delete()
    db.query(ProjectDevice).delete()
    db.commit()


def ver(http_client, token, pid):
    return http_client.get(f"{API}/tracking/projects/{pid}", headers=_auth(token))


def fase(http_client, token, pid, clave, nota=None):
    return http_client.patch(f"{API}/tracking/projects/{pid}/phase", headers=_auth(token),
                             json={"phase": clave, "note": nota})


# --- la vista ---------------------------------------------------------------


def test_un_proyecto_nuevo_empieza_en_la_primera_fase(http_client, mundo):
    v = ver(http_client, mundo["t_a"], mundo["p_infra"]).json()
    assert v["phase"] == "diagnostico"
    assert [f["state"] for f in v["phases"]] == ["current", "todo", "todo", "todo", "todo"]
    assert v["progress_percent"] == 0


def test_cada_linea_lee_el_recorrido_con_sus_palabras(http_client, mundo):
    infra = [f["label"] for f in ver(http_client, mundo["t_a"], mundo["p_infra"]).json()["phases"]]
    dev = [f["label"] for f in ver(http_client, mundo["t_a"], mundo["p_dev"]).json()["phases"]]
    assert infra[0] == "Diagnóstico" and infra[2] == "Implementación"
    assert dev[0] == "Descubrimiento" and dev[2] == "Desarrollo" and dev[4] == "Soporte"
    assert ver(http_client, mundo["t_a"], mundo["p_dev"]).json()["line"] == "dev"
    assert ver(http_client, mundo["t_a"], mundo["p_infra"]).json()["line"] == "infra"


def test_las_claves_de_fase_son_las_mismas_en_las_dos_lineas(http_client, mundo):
    a = [f["key"] for f in ver(http_client, mundo["t_a"], mundo["p_infra"]).json()["phases"]]
    b = [f["key"] for f in ver(http_client, mundo["t_a"], mundo["p_dev"]).json()["phases"]]
    assert a == b == list(fases.CLAVES)


# --- quien ve que -----------------------------------------------------------


def test_un_cliente_no_ve_el_proyecto_de_otro_cliente(http_client, mundo):
    assert ver(http_client, mundo["t_b"], mundo["p_infra"]).status_code == 404
    assert ver(http_client, mundo["t_a"], mundo["p_b"]).status_code == 404


def test_un_colaborador_solo_ve_los_proyectos_donde_es_miembro(http_client, mundo):
    assert ver(http_client, mundo["t_miembro"], mundo["p_infra"]).status_code == 200
    assert ver(http_client, mundo["t_ajeno"], mundo["p_infra"]).status_code == 404
    assert ver(http_client, mundo["t_miembro"], mundo["p_dev"]).status_code == 404


def test_sin_sesion_no_se_ve(http_client, mundo):
    assert http_client.get(f"{API}/tracking/projects/{mundo['p_infra']}").status_code == 401


def test_el_cliente_no_ve_correos_ni_ip(http_client, mundo):
    h = mundo["h"]
    http_client.put(f"{API}/tracking/projects/{mundo['p_infra']}/devices", headers=h,
                    json={"device_ids": [mundo["equipo"].id]})
    texto = ver(http_client, mundo["t_a"], mundo["p_infra"]).text
    assert "fw-seg-a" in texto and "Fortinet" in texto           # ve QUE equipo es
    assert "10.99.99.1" not in texto                              # no como llegar a el
    assert "@ninjasec.local" not in texto and "@cliente.pe" not in texto   # ni correos


def test_el_cliente_ve_el_equipo_y_el_rol_de_quien_trabaja(http_client, mundo):
    v = ver(http_client, mundo["t_a"], mundo["p_infra"]).json()
    assert [(p["name"], p["role"]) for p in v["team"]] == [("Seg-Miembro", "Redes")]


# --- cambiar de fase --------------------------------------------------------


def test_el_especialista_avanza_la_fase_y_queda_en_la_bitacora(http_client, mundo):
    r = fase(http_client, mundo["t_miembro"], mundo["p_infra"], "implementacion", "Empezamos la migracion")
    assert r.status_code == 200, r.text
    v = r.json()
    assert [f["state"] for f in v["phases"]] == ["done", "done", "current", "todo", "todo"]
    cliente = ver(http_client, mundo["t_a"], mundo["p_infra"]).json()
    assert cliente["phase"] == "implementacion"
    assert cliente["updates"][0]["kind"] == "phase_change"
    assert "Implementación" in cliente["updates"][0]["title"]
    assert cliente["updates"][0]["body"] == "Empezamos la migracion"


def test_la_fase_de_desarrollo_se_anuncia_con_su_palabra(http_client, mundo):
    fase(http_client, mundo["h"] and _tok(mundo), mundo["p_dev"], "implementacion")
    titulo = ver(http_client, mundo["t_a"], mundo["p_dev"]).json()["updates"][0]["title"]
    assert "Desarrollo" in titulo


def _tok(mundo):
    return mundo["h"]["Authorization"].split()[1]


def test_una_fase_inventada_se_rechaza(http_client, mundo):
    assert fase(http_client, _tok(mundo), mundo["p_infra"], "celebracion").status_code == 422


def test_el_cliente_no_puede_cambiar_la_fase(http_client, mundo):
    assert fase(http_client, mundo["t_a"], mundo["p_infra"], "transferencia").status_code == 403
    assert ver(http_client, mundo["t_a"], mundo["p_infra"]).json()["phase"] == "diagnostico"


def test_un_colaborador_ajeno_al_proyecto_no_puede_cambiarla(http_client, mundo):
    assert fase(http_client, mundo["t_ajeno"], mundo["p_infra"], "transferencia").status_code == 404


def test_pedir_la_misma_fase_no_duplica_la_bitacora(http_client, mundo):
    fase(http_client, _tok(mundo), mundo["p_infra"], "planificacion")
    fase(http_client, _tok(mundo), mundo["p_infra"], "planificacion")
    cambios = [u for u in ver(http_client, mundo["t_a"], mundo["p_infra"]).json()["updates"]
               if u["kind"] == "phase_change"]
    assert len(cambios) == 1


# --- la bitacora ------------------------------------------------------------


def test_una_nota_interna_no_la_ve_el_cliente(http_client, mundo):
    h = _auth(_tok(mundo))
    http_client.post(f"{API}/tracking/projects/{mundo['p_infra']}/updates", headers=h,
                     json={"title": "Nota interna", "body": "El cliente tarda en responder",
                           "visible_to_client": False})
    http_client.post(f"{API}/tracking/projects/{mundo['p_infra']}/updates", headers=h,
                     json={"title": "Avance visible", "visible_to_client": True})
    cliente = [u["title"] for u in ver(http_client, mundo["t_a"], mundo["p_infra"]).json()["updates"]]
    equipo = [u["title"] for u in ver(http_client, _tok(mundo), mundo["p_infra"]).json()["updates"]]
    assert "Avance visible" in cliente and "Nota interna" not in cliente
    assert {"Avance visible", "Nota interna"} <= set(equipo)
    assert "El cliente tarda" not in ver(http_client, mundo["t_a"], mundo["p_infra"]).text


def test_un_avance_de_desarrollo_lleva_el_enlace_a_la_demo(http_client, mundo):
    http_client.post(f"{API}/tracking/projects/{mundo['p_dev']}/updates", headers=_auth(_tok(mundo)),
                     json={"title": "Primera entrega lista", "kind": "milestone",
                           "link_url": "https://demo.ejemplo.pe/app"})
    u = ver(http_client, mundo["t_a"], mundo["p_dev"]).json()["updates"][0]
    assert u["kind"] == "milestone" and u["link_url"] == "https://demo.ejemplo.pe/app"


def test_un_enlace_que_no_es_una_url_se_rechaza(http_client, mundo):
    r = http_client.post(f"{API}/tracking/projects/{mundo['p_dev']}/updates", headers=_auth(_tok(mundo)),
                         json={"title": "Algo", "link_url": "javascript:alert(1)"})
    assert r.status_code == 422


def test_el_cliente_no_publica_avances(http_client, mundo):
    r = http_client.post(f"{API}/tracking/projects/{mundo['p_infra']}/updates",
                         headers=_auth(mundo["t_a"]), json={"title": "Hola equipo"})
    assert r.status_code == 403


def test_la_bitacora_va_de_lo_mas_nuevo_a_lo_mas_viejo(http_client, mundo):
    h = _auth(_tok(mundo))
    for t in ("Primero", "Segundo", "Tercero"):
        http_client.post(f"{API}/tracking/projects/{mundo['p_infra']}/updates", headers=h, json={"title": t})
    assert [u["title"] for u in ver(http_client, mundo["t_a"], mundo["p_infra"]).json()["updates"]][:3] \
        == ["Tercero", "Segundo", "Primero"]


# --- tareas -----------------------------------------------------------------


def _tarea(http_client, mundo, titulo, asignado=None):
    r = http_client.post(f"{API}/project-tasks/", headers=mundo["h"], json={
        "project_id": mundo["p_infra"], "assigned_user_id": (asignado or mundo["miembro"]).id, "title": titulo})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_la_tarea_nace_en_la_fase_del_proyecto(http_client, mundo):
    fase(http_client, _tok(mundo), mundo["p_infra"], "planificacion")
    _tarea(http_client, mundo, "Disenar VLANs")
    v = ver(http_client, mundo["t_a"], mundo["p_infra"]).json()
    plan = next(f for f in v["phases"] if f["key"] == "planificacion")
    assert (plan["tasks_total"], plan["tasks_done"]) == (1, 0)


def test_lo_que_se_esta_haciendo_ahora_y_quien_lo_hace(http_client, mundo):
    tid = _tarea(http_client, mundo, "Configurar el firewall")
    http_client.patch(f"{API}/project-tasks/{tid}/status", headers=_auth(mundo["t_miembro"]),
                      json={"status": "in_progress"})
    v = ver(http_client, mundo["t_a"], mundo["p_infra"]).json()
    assert [(a["title"], a["person"]) for a in v["now"]] == [("Configurar el firewall", "Seg-Miembro")]
    assert v["team"][0]["working_now"] is True


def test_terminar_una_tarea_queda_en_la_bitacora_y_mueve_el_progreso(http_client, mundo):
    tid = _tarea(http_client, mundo, "Levantar inventario")
    _tarea(http_client, mundo, "Probar la VPN")
    http_client.patch(f"{API}/project-tasks/{tid}/status", headers=_auth(mundo["t_miembro"]),
                      json={"status": "done"})
    v = ver(http_client, mundo["t_a"], mundo["p_infra"]).json()
    assert v["progress_percent"] == 50 and (v["tasks_done"], v["tasks_total"]) == (1, 2)
    assert v["updates"][0]["kind"] == "task_done" and "Levantar inventario" in v["updates"][0]["title"]
    assert v["next_up"] == ["Probar la VPN"]


def test_marcar_hecha_dos_veces_no_duplica_la_entrada(http_client, mundo):
    tid = _tarea(http_client, mundo, "Una sola vez")
    for _ in range(2):
        http_client.patch(f"{API}/project-tasks/{tid}/status", headers=_auth(mundo["t_miembro"]),
                          json={"status": "done"})
    hechas = [u for u in ver(http_client, mundo["t_a"], mundo["p_infra"]).json()["updates"]
              if u["kind"] == "task_done"]
    assert len(hechas) == 1


def test_un_proyecto_completado_muestra_todas_las_fases_hechas(http_client, mundo):
    p = http_client.get(f"{API}/projects/{mundo['p_infra']}", headers=mundo["h"]).json()
    http_client.put(f"{API}/projects/{mundo['p_infra']}", headers=mundo["h"], json={
        "organization_id": p["organization_id"], "client_id": p["client_id"],
        "project_type_id": p["project_type_id"], "service_id": p["service_id"],
        "name": p["name"], "status": "completed"})
    v = ver(http_client, mundo["t_a"], mundo["p_infra"]).json()
    assert all(f["state"] == "done" for f in v["phases"])


# --- equipos ----------------------------------------------------------------


def test_se_enlazan_equipos_de_la_sede_del_cliente(http_client, mundo):
    r = http_client.put(f"{API}/tracking/projects/{mundo['p_infra']}/devices", headers=mundo["h"],
                        json={"device_ids": [mundo["equipo"].id]})
    assert r.status_code == 200, r.text
    assert [d["hostname"] for d in r.json()["devices"]] == ["fw-seg-a"]
    cand = r.json()["candidate_devices"]
    assert cand and cand[0]["linked"] is True


def test_no_se_enlaza_un_equipo_de_otro_cliente(db, http_client, mundo):
    sede_b = ClientSite(client_id=mundo["b"].id, name="Sede B")
    db.add(sede_b)
    db.flush()
    ajeno = Device(hostname="fw-seg-b", site_id=sede_b.id, status="online")
    db.add(ajeno)
    db.commit()
    r = http_client.put(f"{API}/tracking/projects/{mundo['p_infra']}/devices", headers=mundo["h"],
                        json={"device_ids": [ajeno.id]})
    assert r.status_code == 404


def test_quitar_un_equipo_lo_desenlaza(http_client, mundo):
    base = f"{API}/tracking/projects/{mundo['p_infra']}/devices"
    http_client.put(base, headers=mundo["h"], json={"device_ids": [mundo["equipo"].id]})
    r = http_client.put(base, headers=mundo["h"], json={"device_ids": []})
    assert r.json()["devices"] == []


def test_el_cliente_no_ve_la_lista_de_candidatos_ni_los_controles(http_client, mundo):
    v = ver(http_client, mundo["t_a"], mundo["p_infra"]).json()
    assert v["can_manage"] is False and v["candidate_devices"] is None
    assert ver(http_client, mundo["t_miembro"], mundo["p_infra"]).json()["can_manage"] is True


def test_el_cliente_no_enlaza_equipos(http_client, mundo):
    r = http_client.put(f"{API}/tracking/projects/{mundo['p_infra']}/devices",
                        headers=_auth(mundo["t_a"]), json={"device_ids": [mundo["equipo"].id]})
    assert r.status_code == 403


# --- fase de una tarea ------------------------------------------------------


def test_se_reasigna_la_fase_de_una_tarea(http_client, mundo):
    tid = _tarea(http_client, mundo, "Documentar")
    r = http_client.patch(f"{API}/tracking/tasks/{tid}/phase", headers=_auth(mundo["t_miembro"]),
                          json={"phase": "transferencia"})
    assert r.status_code == 200 and r.json()["phase"] == "transferencia"
    assert http_client.patch(f"{API}/tracking/tasks/{tid}/phase", headers=_auth(mundo["t_miembro"]),
                             json={"phase": "inventada"}).status_code == 422
    assert http_client.patch(f"{API}/tracking/tasks/{tid}/phase", headers=_auth(mundo["t_a"]),
                             json={"phase": "diagnostico"}).status_code == 403
    assert http_client.patch(f"{API}/tracking/tasks/{tid}/phase", headers=_auth(mundo["t_ajeno"]),
                             json={"phase": "diagnostico"}).status_code == 404
