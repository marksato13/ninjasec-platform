"""Certificaciones del equipo.

La formacion se hace fuera (Fortinet NSE, Cisco NetAcad, AWS Skill Builder...).
Aqui se registra el resultado y se adjunta el certificado para que el
super_admin lo valide; el cliente ve, en su proyecto, al personal asignado con
sus certificaciones validadas y vigentes.

    GET  /user-certifications/                    las mias (admin: las de la organizacion)
    POST /user-certifications/                    registrar
    PUT  /user-certifications/{id}                editar (revoca la validacion si cambia algo material)
    POST /user-certifications/{id}/verify         validar o rechazar (super_admin)
    POST /user-certifications/{id}/file           adjuntar el certificado (PDF o imagen)
    GET  /user-certifications/{id}/file           descargarlo (duenio o admin; nunca el cliente)
    GET  /user-certifications/matrix              admin: capacidades validadas del equipo
    GET  /projects/{id}/team-certifications       el equipo del proyecto, para el cliente
"""

import json

from app.core.time_utils import utcnow

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, get_current_user, require_roles
from app.common.deps.database import get_db
from app.common.storage import IMAGE_TYPES, storage
from app.common.verification import revoke_verification_if_changed
from app.db.models.client_profile import ClientProfile
from app.db.models.enums import CertificationStatus, RoleCode, SkillStatus
from app.db.models.project import Project
from app.db.models.project_member import ProjectMember
from app.db.models.skill import Skill
from app.db.models.user import User
from app.db.models.user_certification import UserCertification
from app.db.models.user_skill import UserSkill
from app.modules.audit.services.audit_service import AuditService
from app.modules.certifications.schemas import (
    CertificacionPublica,
    FilaMatriz,
    MiembroCertificado,
    SkillEnMatriz,
    UserCertificationCreate,
    UserCertificationRead,
    UserCertificationUpdate,
    UserCertificationVerify,
)

router = APIRouter(prefix="/user-certifications", tags=["certifications"])
equipo_router = APIRouter(prefix="/projects", tags=["certifications"])

_ADMINS = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
_STAFF = (*_ADMINS, RoleCode.COLLABORATOR.value)

CERTIFICADO_TIPOS = {"application/pdf": ".pdf", **IMAGE_TYPES}
CERTIFICADO_MAX = 5 * 1024 * 1024
# El tipo lo declara el navegador; se comprueba tambien la firma del archivo
# para que un ejecutable renombrado a .pdf no pase.
_FIRMAS = {
    "application/pdf": (b"%PDF-",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/webp": (b"RIFF",),
}


def _vigentes_validadas(certs) -> list[CertificacionPublica]:
    ahora = utcnow()
    return [
        CertificacionPublica.model_validate(c)
        for c in certs
        if c.status == CertificationStatus.APPROVED
        and (c.expires_at is None or c.expires_at >= ahora)
    ]


def _certificacion_accesible(
    db: Session, cert_id: int, current_user: CurrentUser
) -> UserCertification:
    """La del propio usuario, o cualquiera de su organizacion si es admin.

    El cliente nunca llega a una certificacion por aqui. Lo ajeno da 404.
    """
    certification = db.get(UserCertification, cert_id)
    if not certification:
        raise HTTPException(status_code=404, detail="Certification not found")
    owner = db.get(User, certification.user_id)
    if not owner or owner.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Certification not found")
    if certification.user_id == current_user.id and current_user.role in _STAFF:
        return certification
    if current_user.role in _ADMINS:
        return certification
    raise HTTPException(status_code=404, detail="Certification not found")


@router.get("/matrix", response_model=list[FilaMatriz])
def team_matrix(
    current_user: CurrentUser = Depends(require_roles(*_ADMINS)),
    db: Session = Depends(get_db),
) -> list[FilaMatriz]:
    """Capacidades validadas del equipo: una fila por persona del staff."""
    personas = db.scalars(
        select(User)
        .where(
            User.organization_id == current_user.organization_id,
            User.role_code.in_(
                [RoleCode.SUPER_ADMIN, RoleCode.ADMIN, RoleCode.COLLABORATOR]
            ),
            User.is_active.is_(True),
        )
        .order_by(User.full_name)
    ).all()
    ids = [p.id for p in personas]
    certs: dict[int, list[UserCertification]] = {i: [] for i in ids}
    skills: dict[int, list[SkillEnMatriz]] = {i: [] for i in ids}
    if ids:
        for c in db.scalars(
            select(UserCertification).where(UserCertification.user_id.in_(ids))
        ):
            certs[c.user_id].append(c)
        for us, nombre in db.execute(
            select(UserSkill, Skill.name)
            .join(Skill, Skill.id == UserSkill.skill_id)
            .where(UserSkill.user_id.in_(ids), UserSkill.status == SkillStatus.APPROVED)
        ):
            skills[us.user_id].append(SkillEnMatriz(name=nombre, level=us.level))
    return [
        FilaMatriz(
            user_id=p.id,
            full_name=p.full_name,
            role=p.role_code.value,
            certifications=_vigentes_validadas(certs[p.id]),
            skills=skills[p.id],
        )
        for p in personas
    ]


@router.get("/", response_model=list[UserCertificationRead])
def list_user_certifications(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserCertificationRead]:
    stmt = select(UserCertification).join(User, User.id == UserCertification.user_id)
    stmt = stmt.where(User.organization_id == current_user.organization_id)
    if current_user.role not in (RoleCode.ADMIN.value, RoleCode.SUPER_ADMIN.value):
        stmt = stmt.where(UserCertification.user_id == current_user.id)
    return [
        UserCertificationRead.model_validate(item) for item in db.scalars(stmt).all()
    ]


@router.post(
    "/", response_model=UserCertificationRead, status_code=status.HTTP_201_CREATED
)
def create_user_certification(
    payload: UserCertificationCreate,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: Session = Depends(get_db),
) -> UserCertificationRead:
    user_id = payload.user_id or current_user.id
    if user_id != current_user.id:
        if current_user.role != RoleCode.SUPER_ADMIN.value:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        target_user = db.scalar(select(User).where(User.id == user_id))
        if (
            not target_user
            or target_user.organization_id != current_user.organization_id
        ):
            raise HTTPException(status_code=404, detail="User not found")

    certification = UserCertification(
        user_id=user_id,
        name=payload.name,
        issuer=payload.issuer,
        credential_id=payload.credential_id,
        url=payload.url,
        status=CertificationStatus.PENDING,
        issued_at=payload.issued_at,
        expires_at=payload.expires_at,
        area=payload.area,
    )
    db.add(certification)
    db.commit()
    db.refresh(certification)
    AuditService(db).record(
        current_user.organization_id,
        "user_certification.created",
        "user_certifications",
        str(certification.id),
        current_user.id,
        metadata_json=json.dumps(
            {"user_id": certification.user_id, "name": certification.name},
            ensure_ascii=True,
        ),
    )
    return UserCertificationRead.model_validate(certification)


@router.put("/{cert_id}", response_model=UserCertificationRead)
def update_user_certification(
    cert_id: int,
    payload: UserCertificationUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserCertificationRead:
    certification = db.scalar(
        select(UserCertification).where(UserCertification.id == cert_id)
    )
    if not certification:
        raise HTTPException(status_code=404, detail="Certification not found")
    if certification.user_id != current_user.id:
        if current_user.role not in (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        target_user = db.scalar(select(User).where(User.id == certification.user_id))
        if (
            not target_user
            or target_user.organization_id != current_user.organization_id
        ):
            raise HTTPException(status_code=404, detail="User not found")

    data = payload.model_dump(exclude_unset=True)

    # 21-P-01 / 17-P-04 — la aprobacion se refiere a lo que el revisor vio.
    # Todos estos campos definen la credencial: si cambia cualquiera, el
    # sello de verificado deja de aplicar y vuelve a la bandeja.
    revoked = revoke_verification_if_changed(
        certification,
        data,
        material_fields=("name", "issuer", "credential_id", "url", "issued_at", "expires_at"),
        pending_value=CertificationStatus.PENDING,
    )

    for field, value in data.items():
        setattr(certification, field, value)
    db.add(certification)
    db.commit()
    db.refresh(certification)
    AuditService(db).record(
        current_user.organization_id,
        "user_certification.updated",
        "user_certifications",
        str(certification.id),
        current_user.id,
        metadata_json=json.dumps(
            {
                "user_id": certification.user_id,
                "name": certification.name,
                "verification_revoked": bool(revoked),
                "changed_fields": revoked,
            },
            ensure_ascii=True,
        ),
    )
    return UserCertificationRead.model_validate(certification)


@router.post("/{cert_id}/verify", response_model=UserCertificationRead)
def verify_user_certification(
    cert_id: int,
    payload: UserCertificationVerify,
    current_user: CurrentUser = Depends(require_roles(RoleCode.SUPER_ADMIN.value)),
    db: Session = Depends(get_db),
) -> UserCertificationRead:
    certification = db.scalar(
        select(UserCertification).where(UserCertification.id == cert_id)
    )
    if not certification:
        raise HTTPException(status_code=404, detail="Certification not found")

    target_user = db.scalar(select(User).where(User.id == certification.user_id))
    if not target_user or target_user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        status_value = CertificationStatus(payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid status") from exc

    certification.status = status_value
    certification.rejection_reason = (
        payload.rejection_reason
        if status_value == CertificationStatus.REJECTED
        else None
    )
    certification.verified_by = current_user.id
    certification.verified_at = utcnow()
    db.add(certification)
    db.commit()
    db.refresh(certification)

    AuditService(db).record(
        current_user.organization_id,
        f"user_certification.{certification.status.value}",
        "user_certifications",
        str(certification.id),
        current_user.id,
        metadata_json=json.dumps(
            {
                "user_id": certification.user_id,
                "name": certification.name,
                "rejection_reason": certification.rejection_reason,
            },
            ensure_ascii=True,
        ),
    )
    return UserCertificationRead.model_validate(certification)


@router.post("/{cert_id}/file", response_model=UserCertificationRead)
async def upload_certificate_file(
    cert_id: int,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: Session = Depends(get_db),
) -> UserCertificationRead:
    """Adjunta (o reemplaza) el certificado: PDF, PNG, JPG o WEBP, hasta 5 MB.

    Cambiar el archivo de una certificacion ya resuelta la devuelve a pendiente:
    lo que se valido fue el archivo anterior.
    """
    certification = _certificacion_accesible(db, cert_id, current_user)
    tipo = (file.content_type or "").lower()
    cabecera = await file.read(12)
    await file.seek(0)
    firmas = _FIRMAS.get(tipo, ())
    if not firmas or not any(cabecera.startswith(f) for f in firmas):
        raise HTTPException(
            status_code=415,
            detail="Solo se aceptan certificados en PDF, PNG, JPG o WEBP",
        )
    saved = await storage.save(
        file,
        f"certifications/{current_user.organization_id}",
        CERTIFICADO_TIPOS,
        max_size=CERTIFICADO_MAX,
    )
    anterior = certification.file_key
    certification.file_key = saved.key
    certification.file_name = saved.original_name
    certification.file_type = saved.content_type
    certification.file_size = saved.size
    revocada = certification.status != CertificationStatus.PENDING
    if revocada:
        certification.status = CertificationStatus.PENDING
        certification.verified_by = None
        certification.verified_at = None
        certification.rejection_reason = None
    db.add(certification)
    db.commit()
    db.refresh(certification)
    AuditService(db).record(
        current_user.organization_id,
        "user_certification.file_uploaded",
        "user_certifications",
        str(certification.id),
        current_user.id,
        metadata_json=json.dumps(
            {
                "user_id": certification.user_id,
                "file_type": saved.content_type,
                "file_size": saved.size,
                "replaced": anterior is not None,
                "verification_revoked": revocada,
            },
            ensure_ascii=True,
        ),
    )
    return UserCertificationRead.model_validate(certification)


@router.get("/{cert_id}/file")
def download_certificate_file(
    cert_id: int,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: Session = Depends(get_db),
) -> FileResponse:
    certification = _certificacion_accesible(db, cert_id, current_user)
    if not certification.file_key:
        raise HTTPException(status_code=404, detail="File not found")
    path = storage.resolve(certification.file_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path,
        media_type=certification.file_type,
        filename=certification.file_name,
        # Se abre en el navegador para revisarlo; nunca se interpreta como HTML.
        content_disposition_type="inline",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@equipo_router.get(
    "/{project_id}/team-certifications", response_model=list[MiembroCertificado]
)
def project_team_certifications(
    project_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MiembroCertificado]:
    """El equipo asignado al proyecto con sus certificaciones validadas y vigentes.

    Pensado para el cliente: no lleva adjuntos, ni codigos de credencial, ni
    correos. Un proyecto ajeno (otra organizacion u otro cliente) da 404.
    """
    project = db.get(Project, project_id)
    if not project or project.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user.role in _ADMINS:
        pass
    elif current_user.role == RoleCode.COLLABORATOR.value:
        miembro = db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == current_user.id,
            )
        )
        if not miembro:
            raise HTTPException(status_code=404, detail="Project not found")
    else:
        perfil = db.scalar(
            select(ClientProfile).where(ClientProfile.user_id == current_user.id)
        )
        if not perfil or project.client_id is None or perfil.client_id != project.client_id:
            raise HTTPException(status_code=404, detail="Project not found")

    filas = db.execute(
        select(ProjectMember, User)
        .join(User, User.id == ProjectMember.user_id)
        .where(
            ProjectMember.project_id == project.id,
            User.organization_id == current_user.organization_id,
            User.is_active.is_(True),
        )
        .order_by(User.full_name)
    ).all()
    ids = [u.id for _, u in filas]
    certs: dict[int, list[UserCertification]] = {i: [] for i in ids}
    if ids:
        for c in db.scalars(
            select(UserCertification).where(UserCertification.user_id.in_(ids))
        ):
            certs[c.user_id].append(c)
    return [
        MiembroCertificado(
            user_id=u.id,
            full_name=u.full_name,
            role_in_project=m.role_in_project or m.project_role,
            certifications=_vigentes_validadas(certs[u.id]),
        )
        for m, u in filas
    ]
