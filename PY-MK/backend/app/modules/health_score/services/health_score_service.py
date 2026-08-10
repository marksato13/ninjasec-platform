from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.client import Client
from app.db.models.enums import FindingStatus
from app.db.models.security_review import ReviewFinding, SecurityReview
from app.modules.hardening.services.evaluation_service import HardeningEvaluationService
from app.modules.risk_scoring.services.scoring_service import RiskScoringService
from app.modules.vulnerability_inventory.services.inventory_service import VulnerabilityInventoryService

_FINDING_WEIGHT = {"critical": 15, "high": 10, "medium": 5, "low": 2, "info": 0}
_HARDENING_WEIGHT = {"critical": 15, "high": 10, "medium": 5, "low": 2}
_OPEN_FINDING_STATUSES = (FindingStatus.OPEN, FindingStatus.IN_PROGRESS)


class HealthScoreService:
    """30-P3: índice de salud 0-100 por cliente, en lenguaje ejecutivo no
    técnico. Combina cuatro señales reales ya construidas en la
    plataforma -- no es una caja negra, cada deducción es explicable:

    1. Hallazgos de revisiones de seguridad abiertos (módulo 06)
    2. Reglas de hardening que fallan (31-P1)
    3. Hosts de alto riesgo por reputación externa + alertas (30-P2/P4)
    4. CVEs de alta probabilidad de explotación -- EPSS >= 0.5 (32-P1)

    Cada categoría tiene un tope de deducción para que ninguna señal por
    sí sola pueda hundir el score a cero -- un cliente con muchos
    hallazgos menores no debería verse igual de mal que uno con pocos
    hallazgos críticos.
    """

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user

    def _client(self, client_id: int) -> Client:
        client = self.db.scalar(select(Client).where(Client.id == client_id, Client.organization_id == self.current_user.organization_id))
        if not client:
            raise HTTPException(404, "Cliente no encontrado")
        return client

    def _findings_deduction(self, client_id: int) -> tuple[int, dict]:
        findings = list(self.db.scalars(
            select(ReviewFinding)
            .join(SecurityReview, ReviewFinding.review_id == SecurityReview.id)
            .where(SecurityReview.client_id == client_id, ReviewFinding.status.in_(_OPEN_FINDING_STATUSES))
        ))
        raw = sum(_FINDING_WEIGHT.get(f.severity.value, 0) for f in findings)
        deduction = min(30, raw)
        return deduction, {"category": "Hallazgos de revisiones abiertos", "count": len(findings), "deduction": deduction}

    def _hardening_deduction(self, client_id: int) -> tuple[int, dict]:
        evaluations = HardeningEvaluationService(self.db, self.current_user).evaluate(client_id)
        fails = [e for e in evaluations if e["result"] == "fail"]
        raw = sum(_HARDENING_WEIGHT.get(e["rule"].severity, 0) for e in fails)
        deduction = min(40, raw)
        return deduction, {"category": "Reglas de hardening incumplidas", "count": len(fails), "deduction": deduction}

    def _risk_hosts_deduction(self, client_id: int) -> tuple[int, dict]:
        hosts = RiskScoringService(self.db, self.current_user).score_client_hosts(client_id)
        high_risk = [h for h in hosts if h["composite_score"] >= 70]
        deduction = min(20, len(high_risk) * 5)
        return deduction, {"category": "Hosts de alto riesgo (reputación + alertas)", "count": len(high_risk), "deduction": deduction}

    def _cve_deduction(self, client_id: int) -> tuple[int, dict]:
        devices = VulnerabilityInventoryService(self.db, self.current_user).list_client_device_cves(client_id)
        high_epss = sum(1 for d in devices for c in d["cves"] if c["epss_score"] >= 0.5)
        deduction = min(10, high_epss * 3)
        return deduction, {"category": "CVEs de alta probabilidad de explotación (EPSS ≥ 0.5)", "count": high_epss, "deduction": deduction}

    def compute(self, client_id: int) -> dict:
        client = self._client(client_id)
        breakdown = []
        score = 100
        for method in (self._findings_deduction, self._hardening_deduction, self._risk_hosts_deduction, self._cve_deduction):
            deduction, detail = method(client_id)
            score -= deduction
            breakdown.append(detail)

        score = max(0, min(100, round(score)))
        if score >= 80:
            label, narrative = "Saludable", "La postura de seguridad del cliente está en buen estado, sin señales que requieran atención inmediata."
        elif score >= 60:
            label, narrative = "Con observaciones", "Hay puntos de atención que conviene resolver en las próximas semanas, sin ser una emergencia."
        else:
            label, narrative = "Requiere atención", "Se detectaron varias señales de riesgo activas — se recomienda priorizar su resolución esta semana."

        return {
            "client_id": client.id,
            "client_name": client.company_name,
            "score": score,
            "label": label,
            "narrative": narrative,
            "breakdown": breakdown,
        }
