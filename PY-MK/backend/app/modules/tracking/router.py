"""Seguimiento de un proyecto: la misma vista para el cliente y para el especialista.

    GET   /tracking/projects/{id}              la vista (se adapta a quien la pide)
    PATCH /tracking/projects/{id}/phase        cambiar de fase                (equipo)
    POST  /tracking/projects/{id}/updates      publicar un avance             (equipo)
    PUT   /tracking/projects/{id}/devices      fijar los equipos del proyecto (equipo)
    PATCH /tracking/tasks/{id}/phase           a que fase pertenece una tarea (equipo)

## Quien ve que

- **Cliente:** solo SU proyecto, y de la bitacora solo lo marcado `visible_to_client`.
  Del equipo ve nombre y rol, **nunca** el correo. De los equipos, **nunca** la IP.
- **Colaborador:** solo los proyectos donde es miembro. Puede avanzar el proyecto.
- **Admin / super admin:** los de su organizacion.

Lo que no le corresponde a quien pregunta devuelve **404**, no 403: no se confirma que
exista. Esa regla es la que impide que un cliente descubra el proyecto de otro.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, get_current_user
from app.common.deps.database import get_db
from app.core import fases
from app.db.models.client_profile import ClientProfile
from app.db.models.client_site import ClientSite
from app.db.models.device import Device
from app.db.models.enums import ProjectStatus, ProjectTaskStatus, RoleCode
from app.db.models.project import Project
from app.db.models.project_member import ProjectMember
from app.db.models.project_task import ProjectTask
from app.db.models.project_tracking import ProjectDevice, ProjectUpdate
from app.db.models.service import Service
from app.db.models.user import User
from app.modules.audit.services.audit_service import AuditService

router = APIRouter(prefix="/tracking", tags=["tracking"])

_ADMINS = {RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value}
Clase = Literal["update", "milestone"]


# --------------------------------------------------------------------------
# Esquemas
# --------------------------------------------------------------------------


class FaseOut(BaseModel):
    key: str
    label: str
    description: str
    state: Literal["done", "current", "todo"]
    tasks_total: int
    tasks_done: int


class AhoraOut(BaseModel):
    task_id: int
    title: str
    person: str
    phase: str | None


class PersonaOut(BaseModel):
    name: str
    role: str | None
    open_tasks: int
    done_tasks: int
    working_now: bool


class EquipoOut(BaseModel):
    id: int
    hostname: str
    type: str | None
    vendor: str | None
    model: str | None
    status: str


class AvanceOut(BaseModel):
    id: int
    kind: str
    phase: str | None
    title: str
    body: str | None
    link_url: str | None
    author: str | None
    created_at: datetime
    visible_to_client: bool


class CandidatoOut(EquipoOut):
    linked: bool


class VistaOut(BaseModel):
    id: int
    name: str
    description: str | None
    line: Literal["dev", "infra"]
    status: str
    phase: str
    paused: bool
    start_date: str | None
    end_date: str | None
    progress_percent: int
    tasks_total: int
    tasks_done: int
    phases: list[FaseOut]
    now: list[AhoraOut]
    next_up: list[str]
    team: list[PersonaOut]
    devices: list[EquipoOut]
    updates: list[AvanceOut]
    last_activity_at: datetime | None
    # Solo para el equipo:
    can_manage: bool
    candidate_devices: list[CandidatoOut] | None = None


class FaseIn(BaseModel):
    phase: str
    note: str | None = Field(default=None, max_length=1000)


class AvanceIn(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    body: str | None = Field(default=None, max_length=4000)
    kind: Clase = "update"
    link_url: HttpUrl | None = None
    visible_to_client: bool = True


class EquiposIn(BaseModel):
    device_ids: list[int] = Field(max_length=100)


class TareaFaseIn(BaseModel):
    phase: str | None


# --------------------------------------------------------------------------
# Acceso
# --------------------------------------------------------------------------


def _cargar(db: Session, user: CurrentUser, project_id: int) -> tuple[Project, bool]:
    """Devuelve (proyecto, puede_gestionar). 404 si no le corresponde a quien pregunta."""
    p = db.get(Project, project_id)
    nada = HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if p is None:
        raise nada
    if user.role in _ADMINS:
        if p.organization_id != user.organization_id:
            raise nada
        return p, True
    if user.role == RoleCode.COLLABORATOR.value:
        es_miembro = db.scalar(select(ProjectMember.id).where(
            ProjectMember.project_id == p.id, ProjectMember.user_id == user.id))
        if es_miembro is None or p.organization_id != user.organization_id:
            raise nada
        return p, True
    if user.role == RoleCode.CLIENT.value:
        perfil = db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
        if perfil is None or p.client_id != perfil.client_id:
            raise nada
        return p, False
    raise nada


def _gestionar(db: Session, user: CurrentUser, project_id: int) -> Project:
    p, puede = _cargar(db, user, project_id)
    if not puede:
        # Un cliente que intenta cambiar algo ve lo mismo que quien no existe.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
    return p


# --------------------------------------------------------------------------
# La vista
# --------------------------------------------------------------------------


def _linea(db: Session, p: Project) -> Literal["dev", "infra"]:
    cat = db.scalar(select(Service.category).where(Service.id == p.service_id)) if p.service_id else None
    return fases.linea_de(cat)


def _equipo_out(d: Device) -> EquipoOut:
    # Sin IP, sin serie, sin responsable: el cliente ve QUE equipo es, no como llegar a el.
    return EquipoOut(id=d.id, hostname=d.hostname, type=d.device_type, vendor=d.vendor,
                     model=d.model, status=d.status or "unknown")


def construir_vista(db: Session, p: Project, puede_gestionar: bool) -> VistaOut:
    linea = _linea(db, p)
    tareas = list(db.scalars(select(ProjectTask).where(ProjectTask.project_id == p.id)).all())
    hechas = [t for t in tareas if t.status == ProjectTaskStatus.DONE]
    completado = p.status == ProjectStatus.COMPLETED
    i_actual = fases.indice(p.phase)

    lista_fases: list[FaseOut] = []
    for i, clave in enumerate(fases.CLAVES):
        rotulo, desc = fases.ROTULOS[linea][clave]
        estado = "done" if (completado or i < i_actual) else ("current" if i == i_actual else "todo")
        de_fase = [t for t in tareas if t.phase == clave]
        lista_fases.append(FaseOut(
            key=clave, label=rotulo, description=desc, state=estado,
            tasks_total=len(de_fase),
            tasks_done=sum(1 for t in de_fase if t.status == ProjectTaskStatus.DONE),
        ))

    nombres = {u.id: u for u in db.scalars(select(User).where(
        User.id.in_({t.assigned_user_id for t in tareas} | set(db.scalars(
            select(ProjectMember.user_id).where(ProjectMember.project_id == p.id)).all())))).all()}

    ahora = [AhoraOut(task_id=t.id, title=t.title,
                      person=nombres[t.assigned_user_id].full_name if t.assigned_user_id in nombres else "—",
                      phase=t.phase)
             for t in tareas if t.status == ProjectTaskStatus.IN_PROGRESS]
    proximas = [t.title for t in tareas
                if t.status == ProjectTaskStatus.PENDING and (t.phase in (None, p.phase))][:3]

    en_curso = {t.assigned_user_id for t in tareas if t.status == ProjectTaskStatus.IN_PROGRESS}
    equipo = []
    for m in db.scalars(select(ProjectMember).where(ProjectMember.project_id == p.id)).all():
        u = nombres.get(m.user_id)
        if u is None:
            continue
        mias = [t for t in tareas if t.assigned_user_id == m.user_id]
        equipo.append(PersonaOut(
            name=u.full_name, role=m.role_in_project or m.project_role,
            open_tasks=sum(1 for t in mias if t.status != ProjectTaskStatus.DONE),
            done_tasks=sum(1 for t in mias if t.status == ProjectTaskStatus.DONE),
            working_now=m.user_id in en_curso))

    ids_eq = list(db.scalars(select(ProjectDevice.device_id).where(ProjectDevice.project_id == p.id)).all())
    equipos = [_equipo_out(d) for d in db.scalars(select(Device).where(Device.id.in_(ids_eq))).all()] if ids_eq else []

    q = select(ProjectUpdate).where(ProjectUpdate.project_id == p.id)
    if not puede_gestionar:
        q = q.where(ProjectUpdate.visible_to_client == True)  # noqa: E712
    avances = db.scalars(q.order_by(ProjectUpdate.created_at.desc(), ProjectUpdate.id.desc()).limit(40)).all()
    autores = {u.id: u.full_name for u in db.scalars(select(User).where(
        User.id.in_({a.author_user_id for a in avances if a.author_user_id}))).all()} if avances else {}

    ultima = max([a.created_at for a in avances] + [t.updated_at for t in tareas if t.updated_at], default=None)

    candidatos = None
    if puede_gestionar and p.client_id:
        ids_sedes = list(db.scalars(select(ClientSite.id).where(ClientSite.client_id == p.client_id)).all())
        if ids_sedes:
            candidatos = [CandidatoOut(**_equipo_out(d).model_dump(), linked=d.id in ids_eq)
                          for d in db.scalars(select(Device).where(Device.site_id.in_(ids_sedes))).all()]
        else:
            candidatos = []

    return VistaOut(
        id=p.id, name=p.name, description=p.description, line=linea,
        status=p.status.value if hasattr(p.status, "value") else str(p.status),
        phase=p.phase, paused=p.status == ProjectStatus.PAUSED,
        start_date=p.start_date.isoformat() if p.start_date else None,
        end_date=p.end_date.isoformat() if p.end_date else None,
        progress_percent=round(100 * len(hechas) / len(tareas)) if tareas else 0,
        tasks_total=len(tareas), tasks_done=len(hechas),
        phases=lista_fases, now=ahora, next_up=proximas, team=equipo, devices=equipos,
        updates=[AvanceOut(id=a.id, kind=a.kind, phase=a.phase, title=a.title, body=a.body,
                           link_url=a.link_url, author=autores.get(a.author_user_id),
                           created_at=a.created_at, visible_to_client=a.visible_to_client)
                 for a in avances],
        last_activity_at=ultima, can_manage=puede_gestionar, candidate_devices=candidatos,
    )


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------


@router.get("/projects/{project_id}", response_model=VistaOut)
def ver_seguimiento(project_id: int, user: CurrentUser = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    p, puede = _cargar(db, user, project_id)
    return construir_vista(db, p, puede)


@router.patch("/projects/{project_id}/phase", response_model=VistaOut)
def cambiar_fase(project_id: int, payload: FaseIn, user: CurrentUser = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    p = _gestionar(db, user, project_id)
    if not fases.es_valida(payload.phase):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            f"Fase desconocida. Las validas son: {', '.join(fases.CLAVES)}.")
    if payload.phase != p.phase:
        anterior, p.phase = p.phase, payload.phase
        rotulo = fases.ROTULOS[_linea(db, p)][payload.phase][0]
        db.add(ProjectUpdate(
            organization_id=p.organization_id, project_id=p.id, author_user_id=user.id,
            kind="phase_change", phase=payload.phase, title=f"Pasamos a: {rotulo}",
            body=payload.note, visible_to_client=True))
        AuditService(db).record(
            organization_id=p.organization_id, action="update", entity_type="project_phase",
            entity_id=str(p.id), user_id=user.id,
            metadata_json=f'{{"de": "{anterior}", "a": "{payload.phase}"}}')
        db.commit()
    return construir_vista(db, p, True)


@router.post("/projects/{project_id}/updates", response_model=VistaOut,
             status_code=status.HTTP_201_CREATED)
def publicar_avance(project_id: int, payload: AvanceIn, user: CurrentUser = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    p = _gestionar(db, user, project_id)
    db.add(ProjectUpdate(
        organization_id=p.organization_id, project_id=p.id, author_user_id=user.id,
        kind=payload.kind, phase=p.phase, title=payload.title, body=payload.body,
        link_url=str(payload.link_url) if payload.link_url else None,
        visible_to_client=payload.visible_to_client))
    db.commit()
    return construir_vista(db, p, True)


@router.put("/projects/{project_id}/devices", response_model=VistaOut)
def fijar_equipos(project_id: int, payload: EquiposIn, user: CurrentUser = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    p = _gestionar(db, user, project_id)
    pedidos = set(payload.device_ids)
    if pedidos:
        # Solo equipos de las sedes DEL CLIENTE de este proyecto: ni de otro cliente ni de
        # otra organizacion. Un id ajeno se trata como inexistente.
        sedes = db.scalars(select(ClientSite.id).where(ClientSite.client_id == p.client_id)).all()
        validos = set(db.scalars(select(Device.id).where(
            Device.id.in_(pedidos), Device.site_id.in_(list(sedes) or [-1]))).all())
        if validos != pedidos:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Device not found")
    actuales = {d.device_id: d for d in db.scalars(
        select(ProjectDevice).where(ProjectDevice.project_id == p.id)).all()}
    for did, fila in actuales.items():
        if did not in pedidos:
            db.delete(fila)
    for did in pedidos - set(actuales):
        db.add(ProjectDevice(project_id=p.id, device_id=did))
    db.commit()
    return construir_vista(db, p, True)


@router.patch("/tasks/{task_id}/phase", response_model=dict)
def fase_de_tarea(task_id: int, payload: TareaFaseIn, user: CurrentUser = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    t = db.get(ProjectTask, task_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    _gestionar(db, user, t.project_id)  # 404 si el proyecto no es suyo, 403 si es cliente
    if payload.phase is not None and not fases.es_valida(payload.phase):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Fase desconocida.")
    t.phase = payload.phase
    db.commit()
    return {"id": t.id, "phase": t.phase}
