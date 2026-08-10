from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import create_access_token, verify_password
from app.core.time_utils import utcnow
from app.db.models.enums import RoleCode
from app.db.models.user import User
from app.db.repositories.users import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.user_repository.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AppError("Invalid credentials", 401)
        user.last_login_at = utcnow()
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate_google(self, credential: str) -> User:
        """Verifica el ID token que Google Identity Services entrega en el
        navegador (respuesta del boton "Sign in with Google") y lo asocia a
        una cuenta ya existente por email.

        Se usa verificacion de ID token, no el flujo completo de
        Authorization Code: Google Identity Services ya hace el intercambio
        con Google en el navegador y entrega un JWT firmado por Google. El
        backend solo valida esa firma contra las claves publicas de Google
        (`verify_oauth2_token`, sin red hacia credenciales propias) y que la
        audiencia (`aud`) coincida con `settings.google_client_id`. No hace
        falta `client_secret` ni `redirect_uri` para este flujo -- son del
        flujo de Authorization Code, que no es el que se implemento aca.

        Politica deliberada: Google solo funciona como METODO DE ENTRADA a
        una cuenta que ya existe (creada por un admin en el modulo de
        Usuarios). No se auto-crea una cuenta nueva a partir de un login de
        Google -- decidir automaticamente a que organizacion asignar a un
        desconocido es una decision de seguridad multi-tenant real, y la
        opcion segura es no tomarla sola.
        """
        if not settings.google_client_id:
            raise AppError("Google login no esta configurado", 503)

        try:
            payload = google_id_token.verify_oauth2_token(
                credential, google_requests.Request(), settings.google_client_id
            )
        except Exception as exc:
            raise AppError("Token de Google invalido", 401) from exc

        if not payload.get("email_verified"):
            raise AppError("El email de Google no esta verificado", 401)

        email = (payload.get("email") or "").strip().lower()
        if not email:
            raise AppError("Token de Google invalido", 401)

        user = self.user_repository.get_by_email(email)
        if not user:
            raise AppError(
                "No existe una cuenta con este email. "
                "Contacta a tu administrador para que te de de alta.",
                404,
            )

        user.last_login_at = utcnow()
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def build_login_response(self, user: User) -> dict[str, object]:
        token = create_access_token(user.email, extra={"role": user.role_code.value})
        redirect_to = (
            "/dashboard"
            if user.role_code in {RoleCode.SUPER_ADMIN, RoleCode.ADMIN}
            else "/portal"
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "redirect_to": redirect_to,
            "user": {
                "id": user.id,
                "name": user.full_name,
                "role": user.role_code.value,
                "email": user.email,
                "job_title": user.job_title or "",
            },
        }
