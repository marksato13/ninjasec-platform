"""02-P-05: push de alertas críticas por WebSocket."""

from __future__ import annotations

import pytest
from starlette.websockets import WebSocketDisconnect

from app.core.security import create_access_token, hash_password
from app.db.models.device import Device
from app.db.models.enums import RoleCode, UserStatus
from app.db.models.integration import Integration
from app.db.models.organization import Organization
from app.db.models.role import Role
from app.db.models.user import User

API = "/api/v1"


def test_token_invalido_cierra_la_conexion(http_client):
    with pytest.raises(WebSocketDisconnect):
        with http_client.websocket_connect(f"{API}/alerts/ws?token=esto-no-es-un-jwt"):
            pass


def test_admin_recibe_alertas_por_websocket(db, http_client, admin_token, seed_data):
    org_id = seed_data["org"].id
    integration = Integration(
        organization_id=org_id, connector_type="snmp",
        name="Integracion ws", base_url="https://collector.invalid",
    )
    db.add(integration)
    db.flush()
    device = Device(
        integration_id=integration.id, hostname="fw-critico-ws",
        status="offline", criticality="critical",
    )
    db.add(device)
    db.commit()

    with http_client.websocket_connect(f"{API}/alerts/ws?token={admin_token}") as ws:
        message = ws.receive_json()
        assert message["type"] == "alerts"
        types = {a["type"] for a in message["data"]}
        assert "critical_device_offline" in types


def test_websocket_no_filtra_por_organization_id_ajeno(db, http_client, seed_data):
    # Un usuario de otra organización no debe recibir las alertas de la
    # organización sembrada en seed_data -- aislamiento multi-tenant.
    other_org = Organization(name="Tenant ws ajeno", slug="tenant-ws-ajeno")
    db.add(other_org)
    db.flush()
    role = db.query(Role).filter(Role.code == RoleCode.ADMIN.value).first()
    other_admin = User(
        organization_id=other_org.id, role_id=role.id,
        full_name="Admin otra org", email="admin-otra-org-ws@ninjasec.local",
        password_hash=hash_password("unused"), role_code=RoleCode.ADMIN,
        status=UserStatus.ACTIVE, is_active=True,
    )
    db.add(other_admin)
    db.commit()
    other_token = create_access_token(other_admin.email)

    org_id = seed_data["org"].id
    integration = Integration(
        organization_id=org_id, connector_type="snmp",
        name="Integracion ws aislamiento", base_url="https://collector.invalid",
    )
    db.add(integration)
    db.flush()
    device = Device(
        integration_id=integration.id, hostname="fw-critico-ws-aislado",
        status="offline", criticality="critical",
    )
    db.add(device)
    db.commit()

    with http_client.websocket_connect(f"{API}/alerts/ws?token={other_token}") as ws:
        message = ws.receive_json()
        assert message["type"] == "alerts"
        assert message["data"] == []
