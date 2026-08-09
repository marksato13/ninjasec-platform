import secrets

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models.collaborator_profile import CollaboratorProfile
from app.db.models.enums import RoleCode, UserStatus
from app.db.models.job_application import JobApplication
from app.db.models.role import Role
from app.db.models.user import User


class HiringService:
    def __init__(self, db: Session):
        self.db = db

    def convert_to_collaborator(
        self, application: JobApplication, organization_id: int
    ) -> CollaboratorProfile:
        normalized_email = application.email.strip().lower()
        existing_user = self.db.scalar(
            select(User).where(func.lower(User.email) == normalized_email)
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un usuario con el email {normalized_email}",
            )

        collaborator_role = self.db.scalar(
            select(Role).where(Role.code == RoleCode.COLLABORATOR.value)
        )
        if not collaborator_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No está configurado el rol de colaborador",
            )

        user = User(
            organization_id=organization_id,
            role_id=collaborator_role.id,
            role_code=RoleCode.COLLABORATOR,
            full_name=application.full_name,
            email=normalized_email,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            job_title=application.desired_role,
            status=UserStatus.ACTIVE,
            is_active=True,
        )
        profile = CollaboratorProfile(
            user=user,
            position_title=application.desired_role,
            skills_json=application.skills_summary,
            portfolio_url=application.portfolio_url,
            phone=application.phone,
            cv_url=application.cv_url,
            source_application_id=application.id,
        )
        self.db.add_all([user, profile])
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un usuario con el email {normalized_email}",
            ) from exc
        return profile
