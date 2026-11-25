from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session

from app.common.deps.database import get_db
from app.core.security import decode_access_token
from app.db.models.enums import UserStatus
from app.db.repositories.users import UserRepository
from app.modules.auth.schemas import CurrentUser


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> CurrentUser:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise credentials_error
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InvalidTokenError as exc:
        raise credentials_error from exc

    user = UserRepository(db).get_by_email(email)
    if not user:
        raise credentials_error

    if not user.is_active or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return CurrentUser(
        id=user.id,
        organization_id=user.organization_id,
        email=user.email,
        role=user.role_code.value,
        full_name=user.full_name,
    )


def get_current_user_optional(
    request: Request, db: Session = Depends(get_db)
) -> CurrentUser | None:
    """Para rutas publicas que se comportan distinto con sesion.

    Sin token, o con uno invalido o caducado, devuelve None: la ruta sigue
    siendo publica y trata a quien llama como anonimo.

    Lee la cabecera a mano y no con OAuth2PasswordBearer(auto_error=False):
    con este ultimo, OpenAPI publica la ruta como si exigiera sesion y el
    contrato (oasdiff) la marca como "ya no admite acceso anonimo".
    """
    esquema, _, token = request.headers.get("authorization", "").partition(" ")
    if esquema.lower() != "bearer" or not token.strip():
        return None
    token = token.strip()
    try:
        return get_current_user(token=token, db=db)
    except HTTPException:
        return None


def require_roles(*allowed_roles: str):
    def dependency(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return current_user

    return dependency
