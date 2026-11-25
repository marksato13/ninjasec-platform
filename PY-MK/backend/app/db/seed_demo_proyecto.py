"""Proyectos de EJEMPLO para ensenar el seguimiento a un cliente real.

La base de produccion nace vacia, a proposito. Sin un caso a la vista, ensenar la «senda ninja»
es explicar con las manos. Esto crea un cliente ficticio con dos proyectos (uno de
infraestructura y otro de desarrollo) y se borra con un comando:

    python -m app.db.seed_demo_proyecto            # crea
    python -m app.db.seed_demo_proyecto --borrar   # deja todo como estaba

## Que garantiza

* **Se ve que es de ejemplo.** El cliente y los proyectos llevan `[EJEMPLO]` en el nombre.
* **Nadie puede entrar con ellos.** El equipo y el contacto del cliente son usuarios
  INACTIVOS con correos `@ejemplo.invalid` (un dominio que no existe) y una contrasena
  aleatoria que no se guarda ni se muestra. No hay credenciales que filtrar.
* **Se borra solo lo marcado.** `--borrar` busca por la marca, nunca por rangos ni por «lo
  ultimo creado», y por eso no puede llevarse datos reales.
* **No toca nada que ya exista**: si el ejemplo ya esta creado, se niega a duplicarlo.

Los equipos (`10.x`) son direcciones privadas inventadas.
"""

from __future__ import annotations

import secrets
import sys
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models.area import Area
from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.client_site import ClientSite
from app.db.models.device import Device
from app.db.models.enums import ProjectStatus, ProjectTaskStatus, RoleCode, UserStatus
from app.db.models.organization import Organization
from app.db.models.project import Project
from app.db.models.project_member import ProjectMember
from app.db.models.project_task import ProjectTask
from app.db.models.project_tracking import ProjectDevice, ProjectUpdate
from app.db.models.project_type import ProjectType
from app.db.models.role import Role
from app.db.models.service import Service
from app.db.models.user import User
from app.db.seed_catalogo_servicios import sembrar_catalogo_servicios

MARCA = "[EJEMPLO]"
DOMINIO = "ejemplo.invalid"
CLIENTE = f"{MARCA} Panadería Demo S.A.C."
SLUG_INFRA = "diagnostico-infraestructura"
SLUG_DEV = "sistemas-a-medida"
SLUG_AREA = "ejemplo-area"   # solo si el servicio no trae area propia
SLUG_TIPO = "ejemplo-tipo"   # solo si el servicio no trae tipo propio


class DemoYaExiste(RuntimeError):
    pass


def _correo(nombre: str) -> str:
    return f"{nombre}@{DOMINIO}"


def _servicio(db: Session, org_id: int, slug: str) -> Service:
    s = db.scalar(select(Service).where(Service.organization_id == org_id, Service.slug == slug))
    if s is None:  # el catalogo aun no esta sembrado: es idempotente
        sembrar_catalogo_servicios(db, org_id)
        s = db.scalar(select(Service).where(Service.organization_id == org_id, Service.slug == slug))
    if s is None:
        raise RuntimeError(f"No existe el servicio '{slug}': revisa el catalogo.")
    return s


def _area_y_tipo(db: Session, org_id: int, svc: Service) -> tuple[int, int]:
    """El area y el tipo del servicio; si no los trae, los de la organizacion; y si no hay, unos marcados.

    Lo marcado lo retira `--borrar`, asi que «dejar todo como estaba» sigue siendo cierto.
    """
    area_id = svc.area_id or db.scalar(select(Area.id).where(Area.organization_id == org_id).order_by(Area.id))
    if area_id is None:
        a = Area(organization_id=org_id, name=f"{MARCA} Área", slug=SLUG_AREA)
        db.add(a)
        db.flush()
        area_id = a.id
    tipo_id = svc.project_type_id or db.scalar(
        select(ProjectType.id).where(ProjectType.organization_id == org_id).order_by(ProjectType.id))
    if tipo_id is None:
        t = ProjectType(organization_id=org_id, name=f"{MARCA} Tipo", slug=SLUG_TIPO, is_active=True)
        db.add(t)
        db.flush()
        tipo_id = t.id
    return area_id, tipo_id


def _rol(db: Session, codigo: RoleCode) -> Role:
    r = db.scalar(select(Role).where(Role.code == codigo.value))
    if r is None:
        raise RuntimeError(f"Falta el rol '{codigo.value}': ¿se ejecutaron las migraciones y el seed base?")
    return r


def _usuario(db: Session, org_id: int, nombre: str, alias: str, rol: RoleCode) -> User:
    # Inactivo y con una clave aleatoria que se descarta: existe para mostrarse, no para entrar.
    u = User(
        organization_id=org_id, role_id=_rol(db, rol).id, full_name=nombre, email=_correo(alias),
        password_hash=hash_password(secrets.token_urlsafe(32)), role_code=rol,
        status=UserStatus.INACTIVE, is_active=False,
    )
    db.add(u)
    db.flush()
    return u


def sembrar_demo(db: Session, organization_id: int | None = None, admin_id: int | None = None) -> dict[str, int]:
    """Crea el ejemplo. `admin_id` firma la bitacora; sin el, el primer super_admin de la organizacion."""
    if organization_id is None:
        org = db.scalar(select(Organization).where(Organization.slug == "ninjasec-internal"))
        if org is None:
            raise RuntimeError("No existe la organización 'ninjasec-internal'.")
        organization_id = org.id
    org_id = organization_id

    if db.scalar(select(Client.id).where(Client.organization_id == org_id, Client.company_name == CLIENTE)):
        raise DemoYaExiste("El ejemplo ya está creado. Bórralo con --borrar antes de volver a crearlo.")

    if admin_id is None:
        admin_id = db.scalar(
            select(User.id).where(User.organization_id == org_id, User.role_code == RoleCode.SUPER_ADMIN,
                                  User.is_active.is_(True)).order_by(User.id)
        )
    if admin_id is None:
        raise RuntimeError("No hay un super_admin activo que firme la bitácora.")

    s_infra = _servicio(db, org_id, SLUG_INFRA)
    s_dev = _servicio(db, org_id, SLUG_DEV)
    ahora = datetime.utcnow()

    ana = _usuario(db, org_id, "Andrea (ejemplo)", "andrea", RoleCode.COLLABORATOR)
    bryan = _usuario(db, org_id, "Bryan (ejemplo)", "bryan", RoleCode.COLLABORATOR)
    joel = _usuario(db, org_id, "Joel (ejemplo)", "joel", RoleCode.COLLABORATOR)
    contacto = _usuario(db, org_id, f"{MARCA} Contacto del cliente", "cliente", RoleCode.CLIENT)

    cli = Client(organization_id=org_id, company_name=CLIENTE)
    db.add(cli)
    db.flush()
    db.add(ClientProfile(client_id=cli.id, user_id=contacto.id))
    sede = ClientSite(client_id=cli.id, name="Local principal")
    db.add(sede)
    db.flush()
    equipos = [
        Device(hostname="fw-ejemplo", vendor="Fortinet", model="60F", device_type="firewall",
               ip_address="10.0.0.1", status="online", site_id=sede.id),
        Device(hostname="sw-ejemplo", vendor="Cisco", model="Catalyst", device_type="switch",
               ip_address="10.0.0.2", status="online", site_id=sede.id),
        Device(hostname="ap-ejemplo", vendor="Ubiquiti", device_type="ap",
               ip_address="10.0.0.3", status="unknown", site_id=sede.id),
    ]
    db.add_all(equipos)
    db.flush()

    def proyecto(nombre: str, desc: str, svc: Service, fase: str, dias: int) -> Project:
        area_id, tipo_id = _area_y_tipo(db, org_id, svc)
        p = Project(
            organization_id=org_id, client_id=cli.id, project_type_id=tipo_id, service_id=svc.id,
            area_id=area_id, name=f"{MARCA} {nombre}", description=desc, status=ProjectStatus.ACTIVE,
            phase=fase, start_date=date.today() - timedelta(days=dias), end_date=date.today() + timedelta(days=30),
        )
        db.add(p)
        db.flush()
        return p

    def bitacora(p: Project, filas: list[tuple]) -> None:
        for kind, fase, titulo, cuerpo, visible, minutos in filas:
            db.add(ProjectUpdate(
                organization_id=org_id, project_id=p.id, author_user_id=admin_id, kind=kind, phase=fase,
                title=titulo, body=cuerpo, visible_to_client=visible, created_at=ahora - timedelta(minutes=minutos),
            ))

    S = ProjectTaskStatus
    # ---- Infraestructura, en Implementacion ----
    p1 = proyecto("Segmentación de la red del local", "Separar el wifi de visitas, la caja y los servidores.",
                  s_infra, "implementacion", 24)
    for usr, rol in ((ana, "Redes"), (bryan, "Seguridad")):
        db.add(ProjectMember(project_id=p1.id, user_id=usr.id, role_in_project=rol))
    db.add_all([ProjectDevice(project_id=p1.id, device_id=e.id) for e in equipos])
    for t, usr, est, fase in [
        ("Inventario de equipos", ana, S.DONE, "diagnostico"),
        ("Mapa de la red actual", ana, S.DONE, "diagnostico"),
        ("Diseño de VLANs y reglas", bryan, S.DONE, "planificacion"),
        ("Plan de migración con vuelta atrás", bryan, S.DONE, "planificacion"),
        ("Configurar el firewall", ana, S.IN_PROGRESS, "implementacion"),
        ("Crear la VLAN de visitas", bryan, S.IN_PROGRESS, "implementacion"),
        ("Pruebas de aislamiento", bryan, S.PENDING, "implementacion"),
        ("Manual para el equipo del cliente", ana, S.PENDING, "transferencia"),
    ]:
        db.add(ProjectTask(organization_id=org_id, project_id=p1.id, assigned_user_id=usr.id, title=t,
                           status=est, phase=fase, updated_at=ahora - timedelta(minutes=5)))
    bitacora(p1, [
        ("update", "diagnostico", "Empezamos el diagnóstico",
         "Visita al local y revisión de los equipos. No se modificó nada.", True, 24 * 60 * 20),
        ("phase_change", "planificacion", "Pasamos a: Planificación",
         "Ya sabemos qué hay y qué falla. Ahora diseñamos la solución.", True, 24 * 60 * 12),
        ("milestone", "planificacion", "Plan aprobado",
         "Acordamos el diseño de VLANs y la ventana de migración del sábado.", True, 24 * 60 * 8),
        ("update", "planificacion", "Nota interna de ejemplo",
         "Esta entrada es interna: el cliente NO la ve. Sirve para enseñar la diferencia.", False, 24 * 60 * 7),
        ("phase_change", "implementacion", "Pasamos a: Implementación",
         "Empezamos a configurar. La ventana de migración sigue siendo el sábado.", True, 60 * 30),
    ])

    # ---- Desarrollo, en Diseno ----
    p2 = proyecto("App de pedidos para la panadería", "Pedidos por celular con aviso al horno.",
                  s_dev, "planificacion", 9)
    db.add(ProjectMember(project_id=p2.id, user_id=joel.id, role_in_project="Desarrollo"))
    db.add(ProjectMember(project_id=p2.id, user_id=ana.id, role_in_project="Diseño UI"))
    for t, usr, est, fase in [
        ("Entrevista con quien atiende el mostrador", joel, S.DONE, "diagnostico"),
        ("Prototipo navegable de la pantalla de pedidos", ana, S.IN_PROGRESS, "planificacion"),
        ("Definir la arquitectura", joel, S.PENDING, "planificacion"),
    ]:
        db.add(ProjectTask(organization_id=org_id, project_id=p2.id, assigned_user_id=usr.id, title=t,
                           status=est, phase=fase, updated_at=ahora - timedelta(hours=1)))
    bitacora(p2, [
        ("phase_change", "planificacion", "Pasamos a: Diseño",
         "Con lo que nos contó el equipo del mostrador, armamos el prototipo.", True, 60 * 48),
        ("milestone", "planificacion", "Prototipo listo para que lo pruebes",
         "Ábrelo desde el celular y dinos qué cambiarías.", True, 60 * 3),
    ])
    db.commit()
    return {"cliente": cli.id, "proyecto_infra": p1.id, "proyecto_dev": p2.id}


def borrar_demo(db: Session, organization_id: int | None = None) -> dict[str, int]:
    """Quita el ejemplo, y solo el ejemplo. No hay borrado en cascada: se va de las hojas a la raiz."""
    if organization_id is None:
        org = db.scalar(select(Organization).where(Organization.slug == "ninjasec-internal"))
        if org is None:
            raise RuntimeError("No existe la organización 'ninjasec-internal'.")
        organization_id = org.id

    cliente = db.scalar(select(Client).where(Client.organization_id == organization_id,
                                             Client.company_name == CLIENTE))
    # Los usuarios se buscan por la marca del dominio; jamas por rango de ids o fecha.
    usuarios = list(db.scalars(select(User).where(User.organization_id == organization_id,
                                                  User.email.like(f"%@{DOMINIO}"))))
    n = {"proyectos": 0, "equipos": 0, "usuarios": 0}
    if cliente is not None:
        pids = list(db.scalars(select(Project.id).where(Project.organization_id == organization_id,
                                                        Project.client_id == cliente.id)))
        if pids:
            for modelo in (ProjectUpdate, ProjectDevice, ProjectTask, ProjectMember):
                db.query(modelo).filter(modelo.project_id.in_(pids)).delete(synchronize_session=False)
            n["proyectos"] = db.query(Project).filter(Project.id.in_(pids)).delete(synchronize_session=False)
        sedes = list(db.scalars(select(ClientSite.id).where(ClientSite.client_id == cliente.id)))
        if sedes:
            n["equipos"] = db.query(Device).filter(Device.site_id.in_(sedes)).delete(synchronize_session=False)
            db.query(ClientSite).filter(ClientSite.id.in_(sedes)).delete(synchronize_session=False)
        db.query(ClientProfile).filter(ClientProfile.client_id == cliente.id).delete(synchronize_session=False)
        db.delete(cliente)
        db.flush()
    db.query(Area).filter(Area.organization_id == organization_id, Area.slug == SLUG_AREA).delete(synchronize_session=False)
    db.query(ProjectType).filter(ProjectType.organization_id == organization_id,
                                 ProjectType.slug == SLUG_TIPO).delete(synchronize_session=False)
    for u in usuarios:
        db.delete(u)
        n["usuarios"] += 1
    db.commit()
    return n


def main(argv: list[str]) -> int:
    from app.db.session import SessionLocal

    borrar = "--borrar" in argv
    with SessionLocal() as db:
        try:
            if borrar:
                print("Ejemplo borrado:", borrar_demo(db))
            else:
                print("Ejemplo creado:", sembrar_demo(db))
                print("Ábrelo como administrador: Proyectos → «[EJEMPLO] …» → Centro de mando → «Ver como lo ve el cliente».")
        except DemoYaExiste as e:
            print(e)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
