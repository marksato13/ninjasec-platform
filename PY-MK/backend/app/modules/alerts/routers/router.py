import asyncio
import logging
from datetime import date, datetime, timedelta

from app.core.time_utils import utcnow

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from jwt import PyJWTError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.core.security import decode_access_token
from app.db.models.client_site import ClientSite
from app.db.models.device import Device
from app.db.models.enums import FindingSeverity, FindingStatus, RoleCode, TicketStatus
from app.db.models.integration import Integration
from app.db.models.organization_alert_threshold import OrganizationAlertThreshold
from app.db.models.security_review import ReviewFinding, ReviewRecommendation, SecurityReview
from app.db.models.support_ticket import SupportTicket
from app.db.repositories.users import UserRepository
from app.db.session import SessionLocal
from app.modules.alerts.schemas import (
    AlertItem,
    AlertRefreshResult,
    AlertThresholds,
    AlertThresholdsUpdate,
)
from app.modules.alerts.services import get_alert_thresholds
from app.modules.audit.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])

_INACTIVE_DEVICE = {"retired", "inactive"}


def read_alert_thresholds(
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> AlertThresholds:
    thresholds = get_alert_thresholds(db, current_user.organization_id)
    return AlertThresholds(**thresholds.__dict__)


def update_alert_thresholds(
    payload: AlertThresholdsUpdate,
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> AlertThresholds:
    org_id = current_user.organization_id
    configured = db.get(OrganizationAlertThreshold, org_id)
    if configured is None:
        configured = OrganizationAlertThreshold(organization_id=org_id)
    configured.overdue_days = payload.overdue_days
    configured.no_review_days = payload.no_review_days
    db.add(configured)
    db.commit()
    db.refresh(configured)
    AuditService(db).record(
        org_id,
        "alerts.thresholds.update",
        "organization_alert_thresholds",
        str(org_id),
        current_user.id,
        metadata_json=(
            f'{{"overdue_days":{configured.overdue_days},'
            f'"no_review_days":{configured.no_review_days}}}'
        ),
    )
    return AlertThresholds(
        overdue_days=configured.overdue_days,
        no_review_days=configured.no_review_days,
    )


router.add_api_route(
    "/thresholds", read_alert_thresholds, methods=["GET"], response_model=AlertThresholds
)
router.add_api_route(
    "/thresholds", update_alert_thresholds, methods=["PUT"], response_model=AlertThresholds
)


# ---------------------------------------------------------------------------
# 8.1 — GET /alerts/active
# ---------------------------------------------------------------------------

def compute_active_alerts(
    db: Session, org_id: int, client_id: int | None = None
) -> list[AlertItem]:
    """Recalcula el conjunto de alertas activas de una organización.

    Compartido por GET /alerts/active y el WebSocket de push (02-P-05) --
    una sola fuente de verdad para el motor derivado, sin tabla.
    """
    now = utcnow()
    alerts: list[AlertItem] = []
    thresholds = get_alert_thresholds(db, org_id)

    alerts.extend(_license_expired_alerts(db, org_id, client_id, now))
    alerts.extend(_critical_finding_alerts(db, org_id, client_id, now))
    alerts.extend(_critical_device_offline_alerts(db, org_id, client_id, now))
    alerts.extend(
        _ticket_overdue_alerts(
            db, org_id, client_id, now, thresholds.overdue_days
        )
    )

    # Ordenar: critical primero, luego warning, luego info
    _order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: _order.get(a.severity, 9))
    return alerts


@router.get("/active", response_model=list[AlertItem])
def get_active_alerts(
    client_id: int | None = None,
    current_user: CurrentUser = Depends(
        require_roles(
            RoleCode.SUPER_ADMIN.value,
            RoleCode.ADMIN.value,
            RoleCode.COLLABORATOR.value,
        )
    ),
    db: Session = Depends(get_db),
) -> list[AlertItem]:
    return compute_active_alerts(db, current_user.organization_id, client_id)


# ---------------------------------------------------------------------------
# 8.2 — POST /alerts/refresh
# ---------------------------------------------------------------------------

@router.post("/refresh", response_model=AlertRefreshResult)
def refresh_alerts(
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> AlertRefreshResult:
    """
    Actualiza estados en batch:
    - Integrations con licencia vencida → status = "risk"
    - Devices sin revisión en >30 días → status = "pending_review"  (Regla 19)
    """
    org_id = current_user.organization_id
    today  = date.today()
    thresholds = get_alert_thresholds(db, org_id)
    cutoff = utcnow() - timedelta(days=thresholds.no_review_days)

    # --- Integrations con licencia vencida → "risk" ---
    expired_stmt = select(Integration).where(
        Integration.organization_id == org_id,
        Integration.license_expires_at.isnot(None),
        Integration.license_expires_at < today,
        Integration.status != "risk",
    )
    expired_integrations = db.scalars(expired_stmt).all()
    for i in expired_integrations:
        i.status = "risk"
        db.add(i)

    # --- Devices sin revisión en >30 días → "pending_review" ---
    # Un device se considera revisado si su integration tiene alguna revisión
    # cerrada con executed_at > (now - 30 días)
    reviewed_integration_ids: set[int] = set(
        db.scalars(
            select(SecurityReview.integration_id)
            .where(
                SecurityReview.organization_id == org_id,
                SecurityReview.executed_at.isnot(None),
                SecurityReview.executed_at >= cutoff,
            )
        ).all()
    )

    unreviewed_stmt = select(Device).join(
        Integration, Device.integration_id == Integration.id
    ).where(
        Integration.organization_id == org_id,
        Device.status.notin_(list(_INACTIVE_DEVICE) + ["pending_review"]),
    )
    unreviewed_devices = [
        d for d in db.scalars(unreviewed_stmt).all()
        if d.integration_id not in reviewed_integration_ids
    ]
    for d in unreviewed_devices:
        d.status = "pending_review"
        db.add(d)

    db.commit()
    AuditService(db).record(
        org_id,
        "alerts.refresh",
        "alerts",
        f"integrations:{len(expired_integrations)},devices:{len(unreviewed_devices)}",
        current_user.id,
    )

    return AlertRefreshResult(
        integrations_marked_risk=len(expired_integrations),
        devices_marked_pending_review=len(unreviewed_devices),
    )


# ---------------------------------------------------------------------------
# 02-P-05 — WebSocket de push para alertas críticas
# ---------------------------------------------------------------------------

_WS_POLL_SECONDS = 12
_ALLOWED_WS_ROLES = {
    RoleCode.SUPER_ADMIN.value,
    RoleCode.ADMIN.value,
    RoleCode.COLLABORATOR.value,
}


def _resolve_ws_user(token: str) -> CurrentUser | None:
    """Misma validación que get_current_user(), pero sin Depends() --
    un WebSocket no tiene header Authorization, el token llega por query
    param (?token=) y se valida acá antes de aceptar la conexión."""
    db = SessionLocal()
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            return None
        user = UserRepository(db).get_by_email(email)
        if not user or not user.is_active or user.role_code.value not in _ALLOWED_WS_ROLES:
            return None
        return CurrentUser(
            id=user.id,
            organization_id=user.organization_id,
            email=user.email,
            role=user.role_code.value,
            full_name=user.full_name,
        )
    except PyJWTError:
        return None
    finally:
        db.close()


def _alert_signature(alerts: list[AlertItem]) -> tuple:
    # created_at cambia en cada recálculo aunque nada haya cambiado
    # realmente -- se excluye de la firma para no emitir de más.
    return tuple(
        (a.type, a.entity_type, a.entity_id, a.severity, a.message) for a in alerts
    )


@router.websocket("/ws")
async def alerts_websocket(websocket: WebSocket, token: str, client_id: int | None = None):
    current_user = await run_in_threadpool(_resolve_ws_user, token)
    if not current_user:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    last_signature: tuple | None = None
    try:
        while True:
            db = SessionLocal()
            try:
                alerts = await run_in_threadpool(
                    compute_active_alerts, db, current_user.organization_id, client_id
                )
            finally:
                db.close()

            signature = _alert_signature(alerts)
            if signature != last_signature:
                last_signature = signature
                await websocket.send_json(
                    {"type": "alerts", "data": [a.model_dump(mode="json") for a in alerts]}
                )
            await asyncio.sleep(_WS_POLL_SECONDS)
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Error en /alerts/ws, cerrando conexión")
        try:
            await websocket.close(code=1011)
        except RuntimeError:
            pass


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------

def _license_expired_alerts(
    db: Session,
    org_id: int,
    client_id: int | None,
    now: datetime,
) -> list[AlertItem]:
    stmt = select(Integration).where(
        Integration.organization_id == org_id,
        Integration.license_expires_at.isnot(None),
        Integration.license_expires_at < date.today(),
    )
    if client_id:
        stmt = stmt.where(Integration.client_id == client_id)

    alerts = []
    for i in db.scalars(stmt).all():
        days_ago = (date.today() - i.license_expires_at).days
        alerts.append(AlertItem(
            type="license_expired",
            severity="critical",
            entity_type="integration",
            entity_id=i.id,
            message=f"Consola '{i.name}' con licencia vencida hace {days_ago} día(s) ({i.license_expires_at})",
            created_at=now,
        ))
    return alerts


def _critical_finding_alerts(
    db: Session,
    org_id: int,
    client_id: int | None,
    now: datetime,
) -> list[AlertItem]:
    # Hallazgos críticos/altos abiertos
    stmt = (
        select(ReviewFinding)
        .join(SecurityReview, ReviewFinding.review_id == SecurityReview.id)
        .where(
            SecurityReview.organization_id == org_id,
            ReviewFinding.severity.in_([FindingSeverity.CRITICAL, FindingSeverity.HIGH]),
            ReviewFinding.status == FindingStatus.OPEN,
        )
    )
    if client_id:
        stmt = stmt.where(SecurityReview.client_id == client_id)

    findings = db.scalars(stmt).all()
    if not findings:
        return []

    # Finding_ids que ya tienen ticket asociado
    finding_ids = [f.id for f in findings]
    ticketed: set[int] = set(
        db.scalars(
            select(SupportTicket.finding_id).where(
                SupportTicket.finding_id.in_(finding_ids)
            )
        ).all()
    )
    # Finding_ids que ya tienen recomendación asociada
    recommended: set[int] = set(
        db.scalars(
            select(ReviewRecommendation.finding_id).where(
                ReviewRecommendation.finding_id.in_(finding_ids)
            )
        ).all()
    )

    alerts = []
    for f in findings:
        if f.id not in ticketed and f.id not in recommended:
            sev_label = str(f.severity).upper()
            alerts.append(AlertItem(
                type="critical_finding_open",
                severity="critical" if str(f.severity) == FindingSeverity.CRITICAL else "warning",
                entity_type="review_finding",
                entity_id=f.id,
                message=f"[{sev_label}] Hallazgo '{f.title}' sin ticket ni recomendación asociada",
                created_at=now,
            ))
    return alerts


def _critical_device_offline_alerts(
    db: Session,
    org_id: int,
    client_id: int | None,
    now: datetime,
) -> list[AlertItem]:
    # 18-P-04: un dispositivo crítico caído es una alerta inmediata, no una
    # que espere el ciclo de /alerts/refresh — se deriva en cada lectura,
    # igual que el resto de alertas de este endpoint.
    stmt = (
        select(Device)
        .outerjoin(Integration, Device.integration_id == Integration.id)
        .outerjoin(ClientSite, Device.site_id == ClientSite.id)
        .where(
            Device.status == "offline",
            Device.criticality == "critical",
            or_(
                Integration.organization_id == org_id,
                ClientSite.client.has(organization_id=org_id),
            ),
        )
    )
    if client_id:
        stmt = stmt.where(
            or_(
                Integration.client_id == client_id,
                ClientSite.client_id == client_id,
            )
        )

    alerts = []
    for d in db.scalars(stmt).all():
        alerts.append(AlertItem(
            type="critical_device_offline",
            severity="critical",
            entity_type="device",
            entity_id=d.id,
            message=f"Dispositivo crítico '{d.hostname}' está offline",
            created_at=now,
        ))
    return alerts


def _ticket_overdue_alerts(
    db: Session,
    org_id: int,
    client_id: int | None,
    now: datetime,
    overdue_days: int,
) -> list[AlertItem]:
    cutoff = utcnow() - timedelta(days=overdue_days)
    stmt = select(SupportTicket).where(
        SupportTicket.organization_id == org_id,
        SupportTicket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS]),
        SupportTicket.opened_at < cutoff,
    )
    if client_id:
        stmt = stmt.where(SupportTicket.client_id == client_id)

    alerts = []
    for t in db.scalars(stmt).all():
        days_open = (now - t.opened_at).days if t.opened_at else 0
        alerts.append(AlertItem(
            type="ticket_overdue",
            severity="warning",
            entity_type="support_ticket",
            entity_id=t.id,
            message=f"Ticket #{t.id} '{t.title}' lleva {days_open} día(s) abierto sin cierre",
            created_at=now,
        ))
    return alerts
