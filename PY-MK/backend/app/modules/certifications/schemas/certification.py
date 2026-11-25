from datetime import datetime
from typing import Literal

from pydantic import Field, computed_field, field_validator, model_validator

from app.common.schemas.base import ORMModel
from app.core.time_utils import utcnow


class UserCertificationRead(ORMModel):
    id: int
    user_id: int
    name: str
    issuer: str | None = None
    credential_id: str | None = None
    url: str | None = None
    status: str
    verified_by: int | None = None
    verified_at: datetime | None = None
    rejection_reason: str | None = None
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime | None = None
    area: str | None = None
    # Del adjunto solo se publica que existe y como se llama; la clave de
    # almacenamiento no sale nunca de la API.
    file_name: str | None = None
    file_type: str | None = None
    file_size: int | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_file(self) -> bool:
        return self.file_name is not None

    # --- Vigencia (21-P-02 / 17-P-05) ----------------------------------
    # `expires_at` se guardaba y nadie lo evaluaba: una certificacion
    # caducada seguia mostrandose como "verificada" al cliente.
    #
    # Se deriva en lectura en lugar de mutar `status` porque:
    #   - no requiere migracion ni job programado,
    #   - no puede desincronizarse (se recalcula en cada respuesta),
    #   - preserva el hecho historico de que si fue aprobada.

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False  # sin fecha de vencimiento = no caduca
        return self.expires_at < utcnow()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def days_until_expiry(self) -> int | None:
        """Dias que faltan. Negativo si ya vencio. None si no caduca."""
        if self.expires_at is None:
            return None
        return (self.expires_at - utcnow()).days

    @computed_field  # type: ignore[prop-decorator]
    @property
    def effective_status(self) -> str:
        """Estado que debe mostrar la UI.

        Una certificacion aprobada pero vencida no es "aprobada" de cara
        al cliente. `status` conserva el valor almacenado; este campo es
        el que hay que pintar.
        """
        if self.status == "approved" and self.is_expired:
            return "expired"
        return self.status


Area = Literal["sec", "dev", "both"]


def _url_publica(value: str | None) -> str | None:
    """El enlace de verificacion se muestra al cliente: solo http(s)."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if not value.lower().startswith(("https://", "http://")):
        raise ValueError("El enlace de verificación debe empezar por https://")
    return value


class UserCertificationCreate(ORMModel):
    name: str = Field(min_length=2, max_length=150)
    issuer: str | None = Field(default=None, max_length=120)
    credential_id: str | None = Field(default=None, max_length=120)
    url: str | None = Field(default=None, max_length=255)
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    user_id: int | None = None
    area: Area | None = None

    @field_validator("url")
    @classmethod
    def validar_url(cls, value: str | None) -> str | None:
        return _url_publica(value)


class UserCertificationUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    issuer: str | None = Field(default=None, max_length=120)
    credential_id: str | None = Field(default=None, max_length=120)
    url: str | None = Field(default=None, max_length=255)
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    area: Area | None = None

    @field_validator("url")
    @classmethod
    def validar_url(cls, value: str | None) -> str | None:
        return _url_publica(value)


class CertificacionPublica(ORMModel):
    """Lo que ve un cliente de una certificacion: sin adjunto ni codigo interno."""

    name: str
    issuer: str | None = None
    area: str | None = None
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    url: str | None = None


class MiembroCertificado(ORMModel):
    user_id: int
    full_name: str
    role_in_project: str | None = None
    certifications: list[CertificacionPublica]


class SkillEnMatriz(ORMModel):
    name: str
    level: str | None = None


class FilaMatriz(ORMModel):
    user_id: int
    full_name: str
    role: str
    certifications: list[CertificacionPublica]
    skills: list[SkillEnMatriz]


class UserCertificationVerify(ORMModel):
    status: str
    rejection_reason: str | None = None

    @field_validator("rejection_reason")
    @classmethod
    def normalize_rejection_reason(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def require_rejection_reason(self) -> "UserCertificationVerify":
        if self.status == "rejected" and not self.rejection_reason:
            raise ValueError("El motivo de rechazo es obligatorio")
        return self
