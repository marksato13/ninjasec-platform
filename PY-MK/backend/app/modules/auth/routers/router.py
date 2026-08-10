from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.common.deps.auth import get_current_user
from app.common.deps.database import get_db
from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.db.models.user import User
from app.modules.auth.schemas import (
    CurrentUser,
    GoogleConfigResponse,
    GoogleLoginRequest,
    LoginRequest,
    LoginResponse,
)
from app.modules.auth.services.auth_service import AuthService
from app.modules.audit.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["auth"])


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    job_title: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    service = AuthService(db)
    user = service.authenticate(payload.email, payload.password)
    return LoginResponse.model_validate(service.build_login_response(user))


@router.get("/google/config", response_model=GoogleConfigResponse)
def google_login_config() -> GoogleConfigResponse:
    """Publico -- el frontend lo usa para decidir si muestra el boton de
    Google. `client_id` no es secreto (viaja igual en el HTML de cualquier
    pagina con el boton de Google), por eso es seguro exponerlo aca."""
    if not settings.google_client_id:
        return GoogleConfigResponse(enabled=False)
    return GoogleConfigResponse(enabled=True, client_id=settings.google_client_id)


@router.post("/google", response_model=LoginResponse)
def login_with_google(payload: GoogleLoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    service = AuthService(db)
    user = service.authenticate_google(payload.credential)
    return LoginResponse.model_validate(service.build_login_response(user))


@router.get("/me", response_model=CurrentUser)
def get_me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user


@router.patch("/profile")
def update_profile(
    payload: ProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = db.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.job_title is not None:
        user.job_title = payload.job_title
    db.commit()
    return {"message": "Profile updated"}


@router.post("/change-password")
def change_password(
    payload: PasswordChange,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = db.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    AuditService(db).record(
        current_user.organization_id,
        "user.password_changed",
        "users",
        str(user.id),
        current_user.id,
    )
    return {"message": "Contraseña actualizada"}


@router.post("/logout")
def logout() -> dict[str, str]:
    return {"message": "Token logout handled client-side"}
