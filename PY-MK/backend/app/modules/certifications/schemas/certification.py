from datetime import datetime

from pydantic import computed_field, field_validator, model_validator

from app.common.schemas.base import ORMModel


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
        return self.expires_at < datetime.utcnow()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def days_until_expiry(self) -> int | None:
        """Dias que faltan. Negativo si ya vencio. None si no caduca."""
        if self.expires_at is None:
            return None
        return (self.expires_at - datetime.utcnow()).days

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


class UserCertificationCreate(ORMModel):
    name: str
    issuer: str | None = None
    credential_id: str | None = None
    url: str | None = None
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    user_id: int | None = None


class UserCertificationUpdate(ORMModel):
    name: str | None = None
    issuer: str | None = None
    credential_id: str | None = None
    url: str | None = None
    issued_at: datetime | None = None
    expires_at: datetime | None = None


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
