"""Umbrales persistidos por organizacion (18-P-02 / 20-P-05)."""

from datetime import timedelta

from app.core.time_utils import utcnow
from app.db.models.client import Client
from app.db.models.enums import TicketPriority, TicketStatus
from app.db.models.organization import Organization
from app.db.models.organization_alert_threshold import OrganizationAlertThreshold
from app.db.models.support_ticket import SupportTicket

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_sin_configuracion_devuelve_los_valores_anteriores(http_client, admin_token):
    response = http_client.get(f"{API}/alerts/thresholds", headers=_auth(admin_token))
    assert response.status_code == 200
    assert response.json() == {"overdue_days": 7, "no_review_days": 30}


def test_admin_actualiza_y_lee_su_configuracion(http_client, admin_token):
    response = http_client.put(
        f"{API}/alerts/thresholds",
        json={"overdue_days": 2, "no_review_days": 14},
        headers=_auth(admin_token),
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"overdue_days": 2, "no_review_days": 14}
    assert http_client.get(
        f"{API}/alerts/thresholds", headers=_auth(admin_token)
    ).json() == response.json()


def test_colaborador_no_puede_leer_ni_actualizar(http_client, collaborator_token):
    headers = _auth(collaborator_token)
    assert http_client.get(f"{API}/alerts/thresholds", headers=headers).status_code == 403
    assert http_client.put(
        f"{API}/alerts/thresholds",
        json={"overdue_days": 1, "no_review_days": 1},
        headers=headers,
    ).status_code == 403


def test_no_admite_umbrales_no_positivos(http_client, admin_token):
    response = http_client.put(
        f"{API}/alerts/thresholds",
        json={"overdue_days": 0, "no_review_days": 30},
        headers=_auth(admin_token),
    )
    assert response.status_code == 422


def test_alertas_aplican_el_cambio_sin_reinicio(
    db, http_client, admin_token, seed_data
):
    org_id = seed_data["org"].id
    client = Client(organization_id=org_id, company_name="Cliente umbrales")
    db.add(client)
    db.flush()
    ticket = SupportTicket(
        organization_id=org_id,
        client_id=client.id,
        title="Ticket configurable",
        priority=TicketPriority.MEDIUM,
        status=TicketStatus.OPEN,
        opened_at=utcnow() - timedelta(days=3),
    )
    db.add(ticket)
    db.commit()

    http_client.put(
        f"{API}/alerts/thresholds",
        json={"overdue_days": 7, "no_review_days": 30},
        headers=_auth(admin_token),
    )
    before = http_client.get(f"{API}/alerts/active", headers=_auth(admin_token)).json()
    assert ticket.id not in {
        a["entity_id"] for a in before if a["type"] == "ticket_overdue"
    }

    http_client.put(
        f"{API}/alerts/thresholds",
        json={"overdue_days": 2, "no_review_days": 30},
        headers=_auth(admin_token),
    )
    after = http_client.get(f"{API}/alerts/active", headers=_auth(admin_token)).json()
    assert ticket.id in {
        a["entity_id"] for a in after if a["type"] == "ticket_overdue"
    }


def test_configuracion_de_otro_tenant_no_se_lee(db, http_client, admin_token):
    other = Organization(name="Tenant umbrales ajeno", slug="tenant-umbrales-ajeno")
    db.add(other)
    db.flush()
    db.add(
        OrganizationAlertThreshold(
            organization_id=other.id, overdue_days=99, no_review_days=98
        )
    )
    db.commit()

    response = http_client.get(f"{API}/alerts/thresholds", headers=_auth(admin_token))
    assert response.json() != {"overdue_days": 99, "no_review_days": 98}
