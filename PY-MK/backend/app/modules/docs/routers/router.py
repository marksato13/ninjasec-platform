import json

from app.core.time_utils import utcnow

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, get_current_user, require_roles
from app.common.deps.database import get_db
from app.common.storage import DOCUMENT_TYPES, storage
from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.doc_type import DocType
from app.db.models.enums import (
    ClientStatus,
    DocScope,
    DocStatus,
    DocVisibility,
    RoleCode,
)
from app.db.models.project import Project
from app.db.models.project_doc import ProjectDoc
from app.db.models.project_member import ProjectMember
from app.modules.audit.services.audit_service import AuditService
from app.modules.docs.schemas import (
    DocTypeCreate,
    DocTypeRead,
    DocTypeUpdate,
    ProjectDocClientDecision,
    ProjectDocCreate,
    ProjectDocRead,
    ProjectDocToggle,
    ProjectDocUpdate,
    ProjectDocVerify,
)

router = APIRouter(prefix="", tags=["docs"])


def _get_client_profile(db: Session, user_id: int) -> ClientProfile | None:
    return db.scalar(select(ClientProfile).where(ClientProfile.user_id == user_id))


def _get_project_member(
    db: Session, project_id: int, user_id: int
) -> ProjectMember | None:
    return db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )


def _reabrir_decision(doc: ProjectDoc) -> None:
    """Una version nueva del documento anula la decision del cliente sobre la anterior."""
    doc.client_decision = None
    doc.client_decision_note = None
    doc.client_decision_by = None
    doc.client_decision_at = None


def _get_accessible_doc(
    db: Session, doc_id: int, current_user: CurrentUser, *, write: bool = False
) -> tuple[ProjectDoc, Project]:
    row = db.execute(
        select(ProjectDoc, Project)
        .join(Project, Project.id == ProjectDoc.project_id)
        .where(ProjectDoc.id == doc_id)
    ).one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    doc, project = row
    if current_user.role in (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value):
        if project.organization_id != current_user.organization_id:
            raise HTTPException(status_code=404, detail="Document not found")
    elif current_user.role == RoleCode.COLLABORATOR.value:
        member = _get_project_member(db, project.id, current_user.id)
        if not member or (write and not member.can_publish_docs):
            raise HTTPException(status_code=404, detail="Document not found")
    else:
        profile = _get_client_profile(db, current_user.id)
        if (
            write
            or not profile
            or project.client_id != profile.client_id
            or not doc.enabled
            or doc.visibility != DocVisibility.CLIENT
            or doc.status == DocStatus.DRAFT
        ):
            raise HTTPException(status_code=404, detail="Document not found")
    return doc, project


@router.get("/doc-types", response_model=list[DocTypeRead])
def list_doc_types(
    _: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocTypeRead]:
    return [
        DocTypeRead.model_validate(item) for item in db.scalars(select(DocType)).all()
    ]


@router.post(
    "/doc-types", response_model=DocTypeRead, status_code=status.HTTP_201_CREATED
)
def create_doc_type(
    payload: DocTypeCreate,
    _: CurrentUser = Depends(require_roles(RoleCode.SUPER_ADMIN.value)),
    db: Session = Depends(get_db),
) -> DocTypeRead:
    existing = db.scalar(select(DocType).where(DocType.name == payload.name))
    if existing:
        return DocTypeRead.model_validate(existing)
    try:
        scope_value = DocScope(payload.scope)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid scope") from exc

    doc_type = DocType(
        name=payload.name, scope=scope_value, is_active=payload.is_active
    )
    db.add(doc_type)
    db.commit()
    db.refresh(doc_type)
    return DocTypeRead.model_validate(doc_type)


@router.put("/doc-types/{doc_type_id}", response_model=DocTypeRead)
def update_doc_type(
    doc_type_id: int,
    payload: DocTypeUpdate,
    _: CurrentUser = Depends(require_roles(RoleCode.SUPER_ADMIN.value)),
    db: Session = Depends(get_db),
) -> DocTypeRead:
    doc_type = db.scalar(select(DocType).where(DocType.id == doc_type_id))
    if not doc_type:
        raise HTTPException(status_code=404, detail="Doc type not found")
    updates = payload.model_dump(exclude_unset=True)
    if "scope" in updates:
        try:
            updates["scope"] = DocScope(updates["scope"])
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid scope") from exc
    for field, value in updates.items():
        setattr(doc_type, field, value)
    db.add(doc_type)
    db.commit()
    db.refresh(doc_type)
    return DocTypeRead.model_validate(doc_type)


@router.get("/project-docs", response_model=list[ProjectDocRead])
def list_project_docs(
    project_id: int | None = Query(default=None),
    visibility: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProjectDocRead]:
    stmt = select(ProjectDoc).join(Project, Project.id == ProjectDoc.project_id)
    if project_id:
        stmt = stmt.where(Project.id == project_id)

    if current_user.role in (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value):
        stmt = stmt.where(Project.organization_id == current_user.organization_id)
    elif current_user.role == RoleCode.COLLABORATOR.value:
        stmt = stmt.join(ProjectMember, ProjectMember.project_id == Project.id).where(
            ProjectMember.user_id == current_user.id
        )
    else:
        profile = _get_client_profile(db, current_user.id)
        if not profile:
            return []
        stmt = stmt.join(Client, Client.id == Project.client_id).where(
            Project.client_id == profile.client_id,
            Client.commercial_status == ClientStatus.ACTIVE,
            ProjectDoc.enabled == True,
            ProjectDoc.visibility == DocVisibility.CLIENT,
            ProjectDoc.status != DocStatus.DRAFT,
        )

    if visibility:
        try:
            visibility_value = DocVisibility(visibility)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid visibility") from exc
        stmt = stmt.where(ProjectDoc.visibility == visibility_value)

    if status_filter:
        try:
            status_value = DocStatus(status_filter)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid status") from exc
        stmt = stmt.where(ProjectDoc.status == status_value)

    return [ProjectDocRead.model_validate(item) for item in db.scalars(stmt).all()]


@router.post(
    "/project-docs", response_model=ProjectDocRead, status_code=status.HTTP_201_CREATED
)
def create_project_doc(
    payload: ProjectDocCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectDocRead:
    project = db.scalar(select(Project).where(Project.id == payload.project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.role in (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value):
        if project.organization_id != current_user.organization_id:
            raise HTTPException(status_code=404, detail="Project not found")
    else:
        member = _get_project_member(db, payload.project_id, current_user.id)
        if not member or not member.can_publish_docs:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    doc_type = db.scalar(select(DocType).where(DocType.id == payload.doc_type_id))
    if not doc_type:
        raise HTTPException(status_code=404, detail="Doc type not found")

    try:
        visibility_value = DocVisibility(payload.visibility)
        status_value = DocStatus(payload.status)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="Invalid visibility or status"
        ) from exc

    doc = ProjectDoc(
        project_id=payload.project_id,
        doc_type_id=payload.doc_type_id,
        title=payload.title,
        summary=payload.summary,
        github_url=payload.github_url,
        preview_md=payload.preview_md,
        visibility=visibility_value,
        status=status_value,
        enabled=payload.enabled,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    AuditService(db).record(
        project.organization_id,
        "project_doc.created",
        "project_docs",
        str(doc.id),
        current_user.id,
        metadata_json=json.dumps(
            {"project_id": doc.project_id, "doc_type_id": doc.doc_type_id},
            ensure_ascii=True,
        ),
    )
    return ProjectDocRead.model_validate(doc)

@router.post("/project-docs/{doc_id}/file", response_model=ProjectDocRead)
async def upload_project_doc_file(
    doc_id: int,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectDocRead:
    doc, project = _get_accessible_doc(db, doc_id, current_user, write=True)
    saved = await storage.save(
        file, f"organizations/{project.organization_id}/documents", DOCUMENT_TYPES
    )
    doc.file_url = f"/api/v1/project-docs/{doc.id}/download"
    doc.file_key = saved.key
    doc.file_name = saved.original_name
    doc.file_type = saved.content_type
    doc.file_size = saved.size
    doc.updated_by = current_user.id
    _reabrir_decision(doc)  # archivo nuevo: el cliente lo vuelve a revisar
    db.commit()
    db.refresh(doc)
    AuditService(db).record(
        project.organization_id,
        "project_doc.file_uploaded",
        "project_docs",
        str(doc.id),
        current_user.id,
        metadata_json=json.dumps({"storage_key": saved.key}, ensure_ascii=True),
    )
    return ProjectDocRead.model_validate(doc)

@router.post("/project-docs/{doc_id}/client-decision", response_model=ProjectDocRead)
def decide_project_doc(
    doc_id: int,
    payload: ProjectDocClientDecision,
    current_user: CurrentUser = Depends(require_roles(RoleCode.CLIENT.value)),
    db: Session = Depends(get_db),
) -> ProjectDocRead:
    """C1: el cliente aprueba un entregable o pide cambios.

    Solo sobre documentos que ya puede ver (de su empresa, visibles para el
    cliente y no borradores); el resto es 404. Una aprobacion es definitiva
    hasta que el equipo sube una version nueva.
    """
    doc, project = _get_accessible_doc(db, doc_id, current_user)
    if doc.client_decision == "approved":
        raise HTTPException(status_code=409, detail="Este documento ya está aprobado.")

    doc.client_decision = payload.decision
    doc.client_decision_note = payload.note
    doc.client_decision_by = current_user.id
    doc.client_decision_at = utcnow()
    db.commit()
    db.refresh(doc)
    AuditService(db).record(
        project.organization_id,
        "project_doc.client_approved" if payload.decision == "approved" else "project_doc.client_changes_requested",
        "project_docs",
        str(doc.id),
        current_user.id,
        metadata_json=json.dumps({"project_id": project.id}, ensure_ascii=True),
    )
    return ProjectDocRead.model_validate(doc)


@router.get("/project-docs/{doc_id}/download")
def download_project_doc_file(
    doc_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    doc, project = _get_accessible_doc(db, doc_id, current_user)
    if not doc.file_url or not doc.file_key:
        raise HTTPException(status_code=404, detail="File not found")
    path = storage.resolve(doc.file_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type=doc.file_type, filename=doc.file_name)


@router.put("/project-docs/{doc_id}", response_model=ProjectDocRead)
def update_project_doc(
    doc_id: int,
    payload: ProjectDocUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectDocRead:
    doc = db.scalar(select(ProjectDoc).where(ProjectDoc.id == doc_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if current_user.role in (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value):
        project = db.scalar(select(Project).where(Project.id == doc.project_id))
        if not project or project.organization_id != current_user.organization_id:
            raise HTTPException(status_code=404, detail="Document not found")
    else:
        # Antes `project` quedaba sin asignar en esta rama: el cambio se guardaba y
        # la auditoria fallaba con 500. Y lo ajeno es 404, no 403.
        member = _get_project_member(db, doc.project_id, current_user.id)
        if not member or not member.can_publish_docs:
            raise HTTPException(status_code=404, detail="Document not found")
        project = db.scalar(select(Project).where(Project.id == doc.project_id))

    updates = payload.model_dump(exclude_unset=True)
    # Si cambia el contenido, el cliente tiene que revisarlo otra vez.
    if updates.keys() & {"title", "summary", "github_url", "preview_md"}:
        _reabrir_decision(doc)
    if "visibility" in updates:
        try:
            updates["visibility"] = DocVisibility(updates["visibility"])
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid visibility") from exc
    if "status" in updates:
        try:
            updates["status"] = DocStatus(updates["status"])
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid status") from exc

    for field, value in updates.items():
        setattr(doc, field, value)
    doc.updated_by = current_user.id
    db.add(doc)
    db.commit()
    db.refresh(doc)

    AuditService(db).record(
        project.organization_id,
        "project_doc.updated",
        "project_docs",
        str(doc.id),
        current_user.id,
        metadata_json=json.dumps(
            {"project_id": doc.project_id, "doc_type_id": doc.doc_type_id},
            ensure_ascii=True,
        ),
    )
    return ProjectDocRead.model_validate(doc)


@router.post("/project-docs/{doc_id}/verify", response_model=ProjectDocRead)
def verify_project_doc(
    doc_id: int,
    payload: ProjectDocVerify,
    current_user: CurrentUser = Depends(require_roles(RoleCode.SUPER_ADMIN.value)),
    db: Session = Depends(get_db),
) -> ProjectDocRead:
    doc = db.scalar(select(ProjectDoc).where(ProjectDoc.id == doc_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    project = db.scalar(select(Project).where(Project.id == doc.project_id))
    if not project or project.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Document not found")

    if payload.status is not None:
        try:
            doc.status = DocStatus(payload.status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid status") from exc
    if payload.enabled is not None:
        doc.enabled = payload.enabled

    doc.verified_by = current_user.id
    doc.verified_at = utcnow()
    db.add(doc)
    db.commit()
    db.refresh(doc)

    AuditService(db).record(
        project.organization_id,
        "project_doc.verified",
        "project_docs",
        str(doc.id),
        current_user.id,
        metadata_json=json.dumps(
            {
                "project_id": doc.project_id,
                "doc_type_id": doc.doc_type_id,
                "enabled": doc.enabled,
                "status": doc.status.value,
            },
            ensure_ascii=True,
        ),
    )
    return ProjectDocRead.model_validate(doc)


@router.post("/project-docs/{doc_id}/toggle", response_model=ProjectDocRead)
def toggle_project_doc(
    doc_id: int,
    payload: ProjectDocToggle,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectDocRead:
    doc = db.scalar(select(ProjectDoc).where(ProjectDoc.id == doc_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if current_user.role in (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value):
        project = db.scalar(select(Project).where(Project.id == doc.project_id))
        if not project or project.organization_id != current_user.organization_id:
            raise HTTPException(status_code=404, detail="Document not found")
    else:
        member = _get_project_member(db, doc.project_id, current_user.id)
        if not member or not member.can_publish_docs:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    doc.enabled = payload.enabled
    doc.updated_by = current_user.id
    db.add(doc)
    db.commit()
    db.refresh(doc)

    AuditService(db).record(
        project.organization_id,
        "project_doc.toggled",
        "project_docs",
        str(doc.id),
        current_user.id,
        metadata_json=json.dumps(
            {"project_id": doc.project_id, "enabled": doc.enabled},
            ensure_ascii=True,
        ),
    )
    return ProjectDocRead.model_validate(doc)
