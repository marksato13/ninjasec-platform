from __future__ import annotations

import json
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.client import Client
from app.db.models.collection_snapshot import CollectionSnapshot
from app.db.models.hardening import HardeningRule
from app.db.models.integration import Integration

_FIREWALL_TYPES = {"pfsense", "fortigate"}


class HardeningEvaluationService:
    """31-P1: evalúa el catálogo de `HardeningRule` contra datos reales del
    cliente (integraciones + eventos normalizados de 30-P1). Las reglas
    `manual` nunca se reportan como pass/fail sin evidencia -- siempre
    "manual", honesto sobre lo que no se puede verificar automáticamente.

    Se calcula en vivo en cada consulta (no se persiste un resultado por
    cliente+regla): evita que un "pass" quede obsoleto si la integración
    se cae o los eventos cambian después de la evaluación."""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user

    def _client(self, client_id: int) -> Client:
        client = self.db.scalar(select(Client).where(Client.id == client_id, Client.organization_id == self.current_user.organization_id))
        if not client:
            raise HTTPException(404, "Cliente no encontrado")
        return client

    def get_client(self, client_id: int) -> Client:
        return self._client(client_id)

    def _integrations(self, client_id: int) -> list[Integration]:
        return list(self.db.scalars(select(Integration).where(Integration.client_id == client_id, Integration.organization_id == self.current_user.organization_id)))

    def _events(self, client_id: int) -> list[dict]:
        integration_ids = [i.id for i in self._integrations(client_id)]
        if not integration_ids:
            return []
        events: list[dict] = []
        for snapshot in self.db.scalars(select(CollectionSnapshot).where(CollectionSnapshot.integration_id.in_(integration_ids))):
            if not snapshot.normalized_payload:
                continue
            try:
                payload = json.loads(snapshot.normalized_payload)
            except ValueError:
                continue
            events.extend(payload.get("events", []))
        return events

    def _check_has_firewall_integration(self, client_id: int) -> tuple[str, str]:
        integrations = self._integrations(client_id)
        active = [i for i in integrations if i.connector_type.lower() in _FIREWALL_TYPES and i.status == "connected"]
        if active:
            return "pass", f"{len(active)} integración(es) de firewall conectada(s): {', '.join(i.name for i in active)}"
        return "fail", "No hay ninguna integración de firewall (pfSense/FortiGate) en estado 'connected'"

    def _check_has_siem_integration(self, client_id: int) -> tuple[str, str]:
        integrations = self._integrations(client_id)
        active = [i for i in integrations if i.connector_type.lower() == "wazuh" and i.status == "connected"]
        if active:
            return "pass", f"Integración SIEM/IDS activa: {active[0].name}"
        return "fail", "No hay ninguna integración Wazuh en estado 'connected'"

    def _check_recent_collection(self, client_id: int) -> tuple[str, str]:
        integration_ids = [i.id for i in self._integrations(client_id)]
        if not integration_ids:
            return "not_applicable", "El cliente no tiene integraciones configuradas"
        cutoff = datetime.utcnow() - timedelta(days=30)
        recent = self.db.scalar(select(CollectionSnapshot).where(CollectionSnapshot.integration_id.in_(integration_ids), CollectionSnapshot.collected_at >= cutoff))
        if recent:
            return "pass", "Hay al menos una recolección de datos en los últimos 30 días"
        return "fail", "No se registró ninguna recolección de datos en los últimos 30 días"

    def _check_no_critical_auth_events(self, client_id: int) -> tuple[str, str]:
        events = self._events(client_id)
        auth_events = [e for e in events if (e.get("event") or {}).get("category") == "authentication"]
        if not auth_events:
            return "not_applicable", "No hay eventos de categoría 'authentication' registrados todavía"
        critical = [e for e in auth_events if (e.get("event") or {}).get("severity") == "critical"]
        if critical:
            return "fail", f"{len(critical)} evento(s) crítico(s) de autenticación (posible fuerza bruta) sin resolver"
        return "pass", f"{len(auth_events)} evento(s) de autenticación, ninguno de severidad crítica"

    def _check_no_critical_malware_events(self, client_id: int) -> tuple[str, str]:
        events = self._events(client_id)
        malware_events = [e for e in events if (e.get("event") or {}).get("category") == "malware"]
        if not malware_events:
            return "not_applicable", "No hay eventos de categoría 'malware' registrados todavía"
        severe = [e for e in malware_events if (e.get("event") or {}).get("severity") in ("critical", "high")]
        if severe:
            return "fail", f"{len(severe)} evento(s) de malware de severidad alta/crítica sin resolver"
        return "pass", f"{len(malware_events)} evento(s) de malware, ninguno de severidad alta/crítica"

    CHECKS = {
        "has_firewall_integration": _check_has_firewall_integration,
        "has_siem_integration": _check_has_siem_integration,
        "recent_collection": _check_recent_collection,
        "no_critical_auth_events": _check_no_critical_auth_events,
        "no_critical_malware_events": _check_no_critical_malware_events,
    }

    def evaluate(self, client_id: int) -> list[dict]:
        self._client(client_id)
        rules = list(self.db.scalars(select(HardeningRule).order_by(HardeningRule.code)))
        results = []
        for rule in rules:
            if rule.verification_method == "manual" or not rule.check_key:
                result, evidence = "manual", "Requiere verificación manual por un consultor -- no hay dato automático disponible."
            else:
                checker = self.CHECKS.get(rule.check_key)
                if not checker:
                    result, evidence = "manual", f"Check '{rule.check_key}' no implementado todavía."
                else:
                    result, evidence = checker(self, client_id)
            results.append({"rule": rule, "result": result, "evidence": evidence})
        return results

    @staticmethod
    def summarize(evaluations: list[dict]) -> dict:
        total = len(evaluations)
        passed = sum(1 for e in evaluations if e["result"] == "pass")
        failed = sum(1 for e in evaluations if e["result"] == "fail")
        manual = sum(1 for e in evaluations if e["result"] == "manual")
        not_applicable = sum(1 for e in evaluations if e["result"] == "not_applicable")
        evaluable = passed + failed
        compliance_percent = round(100 * passed / evaluable, 1) if evaluable else 0.0
        return {"total": total, "passed": passed, "failed": failed, "manual": manual, "not_applicable": not_applicable, "compliance_percent": compliance_percent}
