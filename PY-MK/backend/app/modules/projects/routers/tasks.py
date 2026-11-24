from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.db.models.client_profile import ClientProfile
from app.db.models.enums import ProjectTaskStatus, RoleCode
from app.db.models.project import Project
from app.db.models.project_task import ProjectTask
from app.db.models.project_tracking import ProjectUpdate
from app.db.models.user import User
from app.db.repositories.base import Repository
from app.modules.projects.schemas import (
    ProjectTaskCreate,
    ProjectTaskRead,
    ProjectTaskUpdate,
)

router = APIRouter(prefix="/project-tasks", tags=["project-tasks"])


def registrar_tarea_hecha(db: Session, task: ProjectTask, nuevo: ProjectTaskStatus, actor: CurrentUser) -> None:
    """Cuando una tarea PASA a hecha, queda en la bitacora que ve el cliente.

    Solo en la transicion: marcar dos veces como hecha no escribe dos entradas, y
    reabrirla no borra la entrada anterior (la bitacora cuenta lo que paso).
    """
    if nuevo != ProjectTaskStatus.DONE or task.status == ProjectTaskStatus.DONE:
        return
    quien = db.get(User, task.assigned_user_id)
    db.add(ProjectUpdate(
        organization_id=task.organization_id, project_id=task.project_id, author_user_id=actor.id,
        kind="task_done", phase=task.phase,
        title=f"{(quien.full_name if quien else 'El equipo')} completó: {task.title}"[:160],
        visible_to_client=True))


def _to_read(task: ProjectTask, project: Project, assigned_user: User) -> ProjectTaskRead:
    return ProjectTaskRead(
        id=task.id,
        organization_id=task.organization_id,
        project_id=task.project_id,
        project_name=project.name,
        assigned_user_id=task.assigned_user_id,
        assigned_user_name=assigned_user.full_name,
        title=task.title,
        description=task.description,
        status=task.status.value if isinstance(task.status, ProjectTaskStatus) else task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("/", response_model=list[ProjectTaskRead])
def list_project_tasks(
    project_id: int | None = None,
    current_user: CurrentUser = Depends(
        require_roles(
            RoleCode.SUPER_ADMIN.value,
            RoleCode.ADMIN.value,
            RoleCode.COLLABORATOR.value,
            RoleCode.CLIENT.value,
        )
    ),
    db: Session = Depends(get_db),
) -> list[ProjectTaskRead]:
    stmt = select(ProjectTask, Project, User).join(
        Project, ProjectTask.project_id == Project.id
    ).join(User, ProjectTask.assigned_user_id == User.id)

    if current_user.role == RoleCode.CLIENT.value:
        profile = db.scalar(
            select(ClientProfile).where(ClientProfile.user_id == current_user.id)
        )
        if not profile:
            return []
        stmt = stmt.where(Project.client_id == profile.client_id)
    elif current_user.role == RoleCode.COLLABORATOR.value:
        stmt = stmt.where(ProjectTask.assigned_user_id == current_user.id)
    else:
        stmt = stmt.where(ProjectTask.organization_id == current_user.organization_id)

    if project_id:
        stmt = stmt.where(ProjectTask.project_id == project_id)

    rows = db.execute(stmt).all()
    return [_to_read(task, project, user) for task, project, user in rows]


@router.post("/", response_model=ProjectTaskRead, status_code=status.HTTP_201_CREATED)
def create_project_task(
    payload: ProjectTaskCreate,
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> ProjectTaskRead:
    project = db.scalar(
        select(Project).where(
            Project.id == payload.project_id,
            Project.organization_id == current_user.organization_id,
        )
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    assigned_user = db.scalar(
        select(User).where(
            User.id == payload.assigned_user_id,
            User.organization_id == current_user.organization_id,
        )
    )
    if not assigned_user:
        raise HTTPException(status_code=404, detail="Assigned user not found")

    try:
        status_value = ProjectTaskStatus(payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid status") from exc

    task = ProjectTask(
        organization_id=current_user.organization_id,
        project_id=project.id,
        assigned_user_id=assigned_user.id,
        title=payload.title,
        description=payload.description,
        status=status_value,
        phase=project.phase,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _to_read(task, project, assigned_user)


class TaskStatusIn(BaseModel):
    status: str


@router.patch("/{task_id}/status", response_model=ProjectTaskRead)
def update_my_task_status(
    task_id: int,
    payload: TaskStatusIn,
    current_user: CurrentUser = Depends(
        require_roles(
            RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.COLLABORATOR.value
        )
    ),
    db: Session = Depends(get_db),
) -> ProjectTaskRead:
    """Cambia SOLO el estado de una tarea.

    Existe porque `PUT /project-tasks/{id}` es solo de admin, y eso dejaba al
    colaborador sin forma de decir "termine": veia su tarea y no podia moverla.

    Un colaborador solo puede mover las tareas ASIGNADAS A EL. La de otro
    devuelve 404, no 403: no se confirma que exista. Un admin mueve cualquiera
    de su organizacion. Titulo, descripcion y responsable siguen siendo del admin.
    """
    task = Repository(db).get_by_id(ProjectTask, task_id)
    if not task or task.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role == RoleCode.COLLABORATOR.value and task.assigned_user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        nuevo = ProjectTaskStatus(payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid status") from exc
    registrar_tarea_hecha(db, task, nuevo, current_user)
    task.status = nuevo
    db.add(task)
    db.commit()
    db.refresh(task)
    return _to_read(task, db.get(Project, task.project_id), db.get(User, task.assigned_user_id))


@router.put("/{task_id}", response_model=ProjectTaskRead)
def update_project_task(
    task_id: int,
    payload: ProjectTaskUpdate,
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> ProjectTaskRead:
    task = Repository(db).get_by_id(ProjectTask, task_id)
    if not task or task.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Task not found")

    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.status is not None:
        try:
            nuevo = ProjectTaskStatus(payload.status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid status") from exc
        registrar_tarea_hecha(db, task, nuevo, current_user)
        task.status = nuevo
    if payload.assigned_user_id is not None:
        assigned_user = db.scalar(
            select(User).where(
                User.id == payload.assigned_user_id,
                User.organization_id == current_user.organization_id,
            )
        )
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found")
        task.assigned_user_id = assigned_user.id

    db.add(task)
    db.commit()
    db.refresh(task)

    project = db.get(Project, task.project_id)
    assigned_user = db.get(User, task.assigned_user_id)
    return _to_read(task, project, assigned_user)


@router.delete("/{task_id}")
def delete_project_task(
    task_id: int,
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    task = Repository(db).get_by_id(ProjectTask, task_id)
    if not task or task.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}
