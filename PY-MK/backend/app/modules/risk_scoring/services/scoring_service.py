from __future__ import annotations

import json
from collections import defaultdict
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time_utils import utcnow
from app.db.models.client import Client
from app.db.models.collection_snapshot import CollectionSnapshot
from app.db.models.integration import Integration
from app.db.models.ip_reputation import IpReputationCache
from app.modules.risk_scoring.services.reputation import REPUTATION_CHECKERS

_SEVERITY_WEIGHT = {"critical": 40, "high": 25, "medium": 10, "low": 3}
_CACHE_TTL = timedelta(hours=24)


class RiskScoringService:
    """30-P2: combina reputación externa (AbuseIPDB/VirusTotal/GreyNoise) con
    la frecuencia/severidad de alertas internas (eventos normalizados de
    30-P1) para priorizar qué IP/host atender primero."""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user

    def _client(self, client_id: int) -> Client:
        client = self.db.scalar(select(Client).where(Client.id == client_id, Client.organization_id == self.current_user.organization_id))
        if not client:
            raise HTTPException(404, "Cliente no encontrado")
        return client

    def _internal_events_by_ip(self, client_id: int) -> dict[str, list[str]]:
        integration_ids = list(self.db.scalars(select(Integration.id).where(Integration.client_id == client_id, Integration.organization_id == self.current_user.organization_id)))
        if not integration_ids:
            return {}
        snapshots = self.db.scalars(select(CollectionSnapshot).where(CollectionSnapshot.integration_id.in_(integration_ids)))
        by_ip: dict[str, list[str]] = defaultdict(list)
        for snapshot in snapshots:
            if not snapshot.normalized_payload:
                continue
            try:
                payload = json.loads(snapshot.normalized_payload)
            except ValueError:
                continue
            for event in payload.get("events", []):
                ip = (event.get("source") or {}).get("ip")
                severity = (event.get("event") or {}).get("severity")
                if ip and severity:
                    by_ip[ip].append(severity)
        return by_ip

    def _external_score(self, ip: str) -> tuple[int, list[dict[str, object]]]:
        details: list[dict[str, object]] = []
        scores: list[int] = []
        cutoff = utcnow() - _CACHE_TTL
        for checker in REPUTATION_CHECKERS:
            source = checker.__name__.replace("check_", "")
            cached = self.db.scalar(
                select(IpReputationCache).where(
                    IpReputationCache.ip_address == ip,
                    IpReputationCache.source == source,
                    IpReputationCache.checked_at >= cutoff,
                )
            )
            if cached:
                scores.append(cached.score)
                details.append({"source": source, "score": cached.score, "category": cached.category})
                continue

            result = checker(ip)
            entry = self.db.scalar(select(IpReputationCache).where(IpReputationCache.ip_address == ip, IpReputationCache.source == source))
            if entry:
                entry.score = result["score"]
                entry.category = result["category"]
                entry.checked_at = utcnow()
            else:
                self.db.add(IpReputationCache(ip_address=ip, source=source, score=result["score"], category=result["category"]))
            self.db.commit()
            scores.append(int(result["score"]))
            details.append(result)

        external_score = round(sum(scores) / len(scores)) if scores else 0
        return external_score, details

    def score_client_hosts(self, client_id: int) -> list[dict[str, object]]:
        self._client(client_id)
        events_by_ip = self._internal_events_by_ip(client_id)
        results: list[dict[str, object]] = []
        for ip, severities in events_by_ip.items():
            internal_score = min(100, sum(_SEVERITY_WEIGHT.get(s, 0) for s in severities))
            external_score, external_details = self._external_score(ip)
            composite = round(0.6 * external_score + 0.4 * internal_score)
            results.append({
                "ip_address": ip,
                "internal_alert_count": len(severities),
                "internal_score": internal_score,
                "external_score": external_score,
                "composite_score": composite,
                "external_sources": external_details,
            })
        results.sort(key=lambda item: item["composite_score"], reverse=True)
        return results
