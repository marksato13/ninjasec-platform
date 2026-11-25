from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, get_current_user_optional, require_roles
from app.common.deps.database import get_db
from app.common.rate_limit import rate_limit
from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.project import Project
from app.db.models.project_type import ProjectType
from app.db.models.service import Service
from app.db.models.service_request import ServiceRequest
from app.db.models.enums import ProjectStatus, RoleCode, ServiceRequestStatus
from app.db.repositories.base import Repository
from app.modules.audit.services.audit_service import AuditService
from app.modules.services.schemas import (
    ServiceCreate,
    ServiceRead,
    ServiceRequestConvert,
    ServiceRequestCreate,
    ServiceRequestRead,
    ServiceRequestUpdate,
)

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/", response_model=list[ServiceRead])
def list_services(db: Session = Depends(get_db)) -> list[ServiceRead]:
    return [
        ServiceRead.model_validate(item) for item in Repository(db).list_all(Service)
    ]


@router.post("/", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
def create_service(
    payload: ServiceCreate,
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> ServiceRead:
    if payload.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Organization access denied")
    service = Service(**payload.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return ServiceRead.model_validate(service)


@router.delete("/{service_id}")
def delete_service(
    service_id: int,
    current_user: CurrentUser = Depends(require_roles(RoleCode.SUPER_ADMIN.value)),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    service = Repository(db).get_by_id(Service, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    if service.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Service not found")
    db.delete(service)
    db.commit()
    return {"message": "Service deleted"}


@router.get("/requests", response_model=list[ServiceRequestRead])
def list_service_requests(
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.CLIENT.value)
    ),
    db: Session = Depends(get_db),
) -> list[ServiceRequestRead]:
    stmt = (
        select(ServiceRequest)
        .join(Service, ServiceRequest.service_id == Service.id)
        .where(Service.organization_id == current_user.organization_id)
    )
    if current_user.role == RoleCode.CLIENT.value:
        # Auditoria 2026-11-25 (A3): antes se filtraba por requester_email, un
        # dato que escribe cualquiera en el formulario publico. Asi un anonimo
        # podia plantar un mensaje (phishing) en el portal de un cliente real.
        # Ahora el cliente solo ve lo enlazado a SU client_id.
        client_id = _client_id_of(db, current_user)
        if client_id is None:
            return []
        stmt = stmt.where(ServiceRequest.client_id == client_id)
    return [ServiceRequestRead.model_validate(item) for item in db.scalars(stmt).all()]


# Auditoria 2026-11-25 (B3): formulario publico sin sesion.
public_request_limit = rate_limit(max_requests=5, window_seconds=3600, name="service-request")


@router.post(
    "/requests",
    response_model=ServiceRequestRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(public_request_limit)],
)
def create_service_request(
    payload: ServiceRequestCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser | None = Depends(get_current_user_optional),
) -> ServiceRequestRead:
    data = payload.model_dump()
    # El client_id nunca lo decide quien envia el formulario: un cliente con
    # sesion queda enlazado a su empresa y a su correo; un anonimo, a ninguna.
    data["client_id"] = None
    if current_user and current_user.role == RoleCode.CLIENT.value:
        data["client_id"] = _client_id_of(db, current_user)
        data["requester_email"] = current_user.email
    req = ServiceRequest(**{**data, "status": ServiceRequestStatus.NEW})
    db.add(req)
    db.commit()
    db.refresh(req)
    return ServiceRequestRead.model_validate(req)


@router.patch("/requests/{request_id}", response_model=ServiceRequestRead)
def update_service_request(
    request_id: int,
    payload: ServiceRequestUpdate,
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> ServiceRequestRead:
    req = Repository(db).get_by_id(ServiceRequest, request_id)
    service = db.get(Service, req.service_id) if req else None
    # A4: la solicitud de otra organizacion no existe para este admin.
    if not req or not service or service.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Service request not found")
    try:
        req.status = ServiceRequestStatus(payload.status)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid status: {payload.status}")
    db.commit()
    db.refresh(req)
    return ServiceRequestRead.model_validate(req)


@router.post(
    "/requests/{request_id}/convert",
    response_model=ServiceRequestRead,
    status_code=status.HTTP_201_CREATED,
)
def convert_service_request(
    request_id: int,
    payload: ServiceRequestConvert,
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> ServiceRequestRead:
    """Solicitud aprobada -> proyecto (auditoria funcional A6).

    Cierra el embudo lead -> cliente -> solicitud -> proyecto: crea el proyecto con
    el servicio y el area de la solicitud, la enlaza y la cierra. Igual que el alta
    manual de proyectos: sin colaboradores el proyecto nace en `planning`.
    """
    req = db.scalar(select(ServiceRequest).where(ServiceRequest.id == request_id).with_for_update())
    service = db.get(Service, req.service_id) if req else None
    if not req or not service or service.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Service request not found")
    if req.project_id is not None:
        raise HTTPException(status_code=409, detail="Service request already converted")
    if not service.area_id:
        raise HTTPException(status_code=400, detail="The service has no area (Ninja Sec / Ninja Dev)")

    client_id = req.client_id or payload.client_id
    if client_id is None:
        raise HTTPException(status_code=422, detail="client_id is required for a public request")
    client = db.scalar(
        select(Client).where(Client.id == client_id, Client.organization_id == current_user.organization_id)
    )
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    project_type = db.get(ProjectType, payload.project_type_id)
    # Los tipos de proyecto son globales (sin organizacion) o de una organizacion.
    if not project_type or project_type.organization_id not in (None, current_user.organization_id):
        raise HTTPException(status_code=404, detail="Project type not found")

    project = Project(
        organization_id=current_user.organization_id,
        client_id=client.id,
        project_type_id=payload.project_type_id,
        area_id=service.area_id,
        service_id=service.id,
        name=payload.name or f"{service.title} · {client.company_name}"[:160],
        description=payload.description or (req.message[:255] if req.message else None),
        status=ProjectStatus.PLANNING,
    )
    db.add(project)
    db.flush()
    req.project_id = project.id
    req.client_id = client.id
    req.status = ServiceRequestStatus.CLOSED
    db.commit()
    db.refresh(req)
    AuditService(db).record(
        current_user.organization_id,
        "service_request.converted",
        "service_requests",
        str(req.id),
        current_user.id,
    )
    return ServiceRequestRead.model_validate(req)


def _client_id_of(db: Session, current_user: CurrentUser) -> int | None:
    profile = db.scalar(select(ClientProfile).where(ClientProfile.user_id == current_user.id))
    return profile.client_id if profile else None
