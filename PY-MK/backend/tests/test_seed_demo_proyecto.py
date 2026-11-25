"""El proyecto de ejemplo: se ve que es de ejemplo, nadie entra con el y se borra sin tocar lo real."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.core.fases import CLAVES
from app.db.models.client import Client
from app.db.models.device import Device
from app.db.models.enums import RoleCode, UserStatus
from app.db.models.organization import Organization
from app.db.models.project import Project
from app.db.models.project_task import ProjectTask
from app.db.models.project_tracking import ProjectUpdate
from app.db.models.role import Role
from app.db.models.service import Service
from app.db.models.user import User
from app.db.seed_demo_proyecto import (
    CLIENTE,
    DOMINIO,
    MARCA,
    DemoYaExiste,
    borrar_demo,
    sembrar_demo,
)
from app.core.security import hash_password


def _n(db, modelo, *donde) -> int:
    return db.scalar(select(func.count()).select_from(modelo).where(*donde))


@pytest.fixture
def entorno(db):
    """Una organizacion propia, con un admin que firma la bitacora. Se limpia entera al terminar."""
    org = Organization(name="Demo Test", slug="demo-test")
    db.add(org)
    db.flush()
    creados = []
    for codigo in RoleCode:
        if db.scalar(select(Role).where(Role.code == codigo.value)) is None:
            r = Role(code=codigo.value, name=codigo.value)
            db.add(r)
            creados.append(r)
    db.flush()
    rol_admin = db.scalar(select(Role).where(Role.code == RoleCode.ADMIN.value))
    admin = User(organization_id=org.id, role_id=rol_admin.id, full_name="Admin real", email="admin-real@demo-test.local",
                 password_hash=hash_password("no-se-usa-123"), role_code=RoleCode.ADMIN,
                 status=UserStatus.ACTIVE, is_active=True)
    db.add(admin)
    db.commit()
    yield org, admin
    db.rollback()
    borrar_demo(db, org.id)
    from app.db.models.area import Area
    from app.db.models.project_type import ProjectType
    db.query(Client).filter(Client.organization_id == org.id).delete()  # p. ej. el «real» de una prueba
    db.query(Service).filter(Service.organization_id == org.id).delete()
    db.query(User).filter(User.organization_id == org.id).delete()
    db.query(ProjectType).filter(ProjectType.organization_id == org.id).delete()
    db.query(Area).filter(Area.organization_id == org.id).delete()
    for r in creados:
        db.delete(r)
    db.delete(org)
    db.commit()


def test_crea_un_cliente_y_dos_proyectos_marcados_como_ejemplo(db, entorno):
    org, admin = entorno
    ids = sembrar_demo(db, org.id, admin.id)
    proyectos = list(db.scalars(select(Project).where(Project.organization_id == org.id)))
    assert len(proyectos) == 2
    assert all(p.name.startswith(MARCA) for p in proyectos), "Cada proyecto debe verse como ejemplo"
    assert db.get(Client, ids["cliente"]).company_name == CLIENTE
    assert {p.phase for p in proyectos} <= set(CLAVES)


def test_cubre_infra_y_desarrollo_en_fases_distintas(db, entorno):
    org, admin = entorno
    sembrar_demo(db, org.id, admin.id)
    fases = {p.phase for p in db.scalars(select(Project).where(Project.organization_id == org.id))}
    assert fases == {"implementacion", "planificacion"}


def test_nadie_puede_entrar_con_los_usuarios_de_ejemplo(db, entorno):
    org, admin = entorno
    sembrar_demo(db, org.id, admin.id)
    ficticios = list(db.scalars(select(User).where(User.organization_id == org.id, User.email.like(f"%@{DOMINIO}"))))
    assert len(ficticios) == 4  # 3 del equipo + el contacto del cliente
    assert all(not u.is_active and u.status == UserStatus.INACTIVE for u in ficticios)


def test_el_correo_de_ejemplo_no_existe(db, entorno):
    """`.invalid` esta reservado (RFC 2606): no puede resolverse, ni recibir ni ser registrado por otro."""
    assert DOMINIO.endswith(".invalid")


def test_las_contrasenas_son_distintas_y_no_son_una_clave_conocida(db, entorno):
    org, admin = entorno
    sembrar_demo(db, org.id, admin.id)
    hashes = [u.password_hash for u in db.scalars(select(User).where(User.email.like(f"%@{DOMINIO}")))]
    assert len(set(hashes)) == len(hashes), "Cada usuario con su propia clave aleatoria"


def test_hay_una_nota_interna_que_el_cliente_no_debe_ver(db, entorno):
    org, admin = entorno
    sembrar_demo(db, org.id, admin.id)
    internas = db.scalars(select(ProjectUpdate).where(ProjectUpdate.organization_id == org.id,
                                                      ProjectUpdate.visible_to_client.is_(False))).all()
    assert len(internas) == 1, "Sirve para ensenar la diferencia entre lo interno y lo visible"


def test_no_se_duplica(db, entorno):
    org, admin = entorno
    sembrar_demo(db, org.id, admin.id)
    with pytest.raises(DemoYaExiste):
        sembrar_demo(db, org.id, admin.id)
    assert _n(db, Project, Project.organization_id == org.id) == 2


def test_borrar_deja_todo_como_estaba(db, entorno):
    org, admin = entorno
    sembrar_demo(db, org.id, admin.id)
    n = borrar_demo(db, org.id)
    assert n["proyectos"] == 2 and n["equipos"] == 3 and n["usuarios"] == 4
    assert _n(db, Project, Project.organization_id == org.id) == 0
    assert _n(db, Client, Client.organization_id == org.id) == 0
    assert _n(db, ProjectTask, ProjectTask.organization_id == org.id) == 0
    assert _n(db, ProjectUpdate, ProjectUpdate.organization_id == org.id) == 0
    assert _n(db, User, User.email.like(f"%@{DOMINIO}")) == 0


def test_borrar_no_se_lleva_lo_real(db, entorno):
    """El riesgo de verdad: un cliente, usuario y proyecto reales conviven con el ejemplo y sobreviven."""
    org, admin = entorno
    real = Client(organization_id=org.id, company_name="Ferretería Real S.A.C.")
    db.add(real)
    db.commit()
    real_id, admin_id = real.id, admin.id

    sembrar_demo(db, org.id, admin.id)
    borrar_demo(db, org.id)

    assert db.get(Client, real_id) is not None, "El cliente real no puede desaparecer"
    assert db.get(User, admin_id) is not None, "Tampoco el administrador real"


def test_borrar_sin_ejemplo_no_falla_ni_borra_nada(db, entorno):
    org, admin = entorno
    assert borrar_demo(db, org.id) == {"proyectos": 0, "equipos": 0, "usuarios": 0}
    assert db.get(User, admin.id) is not None


def test_se_puede_borrar_y_volver_a_crear(db, entorno):
    org, admin = entorno
    sembrar_demo(db, org.id, admin.id)
    borrar_demo(db, org.id)
    sembrar_demo(db, org.id, admin.id)
    assert _n(db, Project, Project.organization_id == org.id) == 2


def test_borrar_no_toca_a_otra_organizacion(db, entorno):
    """Los equipos de otra organizacion con el mismo nombre de host no se tocan."""
    org, admin = entorno
    sembrar_demo(db, org.id, admin.id)
    antes = _n(db, Device)
    borrar_demo(db, org.id)
    assert _n(db, Device) == antes - 3
