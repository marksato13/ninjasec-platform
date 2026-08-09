"""30-P2: scoring de riesgo por IP/host combinando reputación externa
(simulada sin API keys) con la frecuencia/severidad de eventos internos."""

import json

from sqlalchemy import select

from app.db.models.client import Client
from app.db.models.collection_snapshot import CollectionSnapshot
from app.db.models.integration import Integration
from app.db.models.ip_reputation import IpReputationCache

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _client_with_events(db, organization_id, events_by_snapshot):
    client = Client(organization_id=organization_id, company_name="Cliente scoring")
    db.add(client)
    db.commit()

    integration = Integration(
        organization_id=organization_id, client_id=client.id, connector_type="wazuh",
        name="Wazuh scoring", base_url="https://wazuh.example.test",
    )
    db.add(integration)
    db.commit()

    for events in events_by_snapshot:
        db.add(CollectionSnapshot(
            integration_id=integration.id, snapshot_type="security_alerts",
            raw_payload="{}", normalized_payload=json.dumps({"events": events}),
        ))
    db.commit()
    return client


def test_score_combina_severidad_interna_con_reputacion_externa(db, http_client, admin_token, seed_data):
    events = [
        [
            {"event": {"category": "authentication", "severity": "critical"}, "source": {"ip": "198.51.100.23"}, "rule": {"description": "fuerza bruta"}},
            {"event": {"category": "malware", "severity": "high"}, "source": {"ip": "198.51.100.23"}, "rule": {"description": "malware"}},
        ],
    ]
    client = _client_with_events(db, seed_data["org"].id, events)

    response = http_client.get(f"{API}/risk-scoring/hosts?client_id={client.id}", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    hosts = response.json()
    assert len(hosts) == 1
    host = hosts[0]
    assert host["ip_address"] == "198.51.100.23"
    assert host["internal_alert_count"] == 2
    assert host["internal_score"] == 40 + 25  # critical + high
    assert 0 <= host["external_score"] <= 100
    assert len(host["external_sources"]) == 3
    assert host["composite_score"] == round(0.6 * host["external_score"] + 0.4 * host["internal_score"])


def test_hosts_sin_ip_se_ignoran(db, http_client, admin_token, seed_data):
    events = [[{"event": {"category": "network_traffic", "severity": "low"}, "source": {"ip": None}, "rule": {"description": "sin ip"}}]]
    client = _client_with_events(db, seed_data["org"].id, events)

    response = http_client.get(f"{API}/risk-scoring/hosts?client_id={client.id}", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    assert response.json() == []


def test_reputacion_externa_se_cachea_y_no_se_duplica(db, http_client, admin_token, seed_data):
    events = [[{"event": {"category": "malware", "severity": "high"}, "source": {"ip": "203.0.113.9"}, "rule": {"description": "x"}}]]
    client = _client_with_events(db, seed_data["org"].id, events)

    first = http_client.get(f"{API}/risk-scoring/hosts?client_id={client.id}", headers=_auth(admin_token))
    assert first.status_code == 200, first.text
    cache_rows_after_first = db.scalars(select(IpReputationCache).where(IpReputationCache.ip_address == "203.0.113.9")).all()
    assert len(cache_rows_after_first) == 3  # abuseipdb + virustotal + greynoise

    second = http_client.get(f"{API}/risk-scoring/hosts?client_id={client.id}", headers=_auth(admin_token))
    assert second.status_code == 200, second.text
    assert first.json()[0]["composite_score"] == second.json()[0]["composite_score"]
    cache_rows_after_second = db.scalars(select(IpReputationCache).where(IpReputationCache.ip_address == "203.0.113.9")).all()
    assert len(cache_rows_after_second) == 3  # no se duplicó, se reutilizó el caché


def test_rechaza_cliente_de_otra_organizacion(db, http_client, admin_token, seed_data):
    from app.db.models.organization import Organization

    foreign_org = Organization(name="Organizacion Scoring Ajena", slug="scoring-ajena")
    db.add(foreign_org)
    db.commit()
    foreign_client = _client_with_events(db, foreign_org.id, [])

    response = http_client.get(f"{API}/risk-scoring/hosts?client_id={foreign_client.id}", headers=_auth(admin_token))
    assert response.status_code == 404
