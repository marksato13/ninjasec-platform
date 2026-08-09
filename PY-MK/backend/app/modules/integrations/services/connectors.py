import json

from app.core.time_utils import utcnow

# 30-P1: esquema normalizado común (ECS-lite) para snapshot.normalized_payload.
#
# Antes, cada connector_type tenía su propio formato de normalized_payload sin
# ninguna clave en común (pfSense: uptime_status/active_vpn_sessions,
# FortiGate: threat_events/blocked_intrusions) -- imposible correlacionar
# eventos entre fuentes. Ahora las tres fuentes (pfSense, FortiGate, Wazuh)
# devuelven la misma envoltura: una lista de eventos con un subconjunto de
# Elastic Common Schema (ECS): event.category, event.severity, source.ip,
# rule.description, @timestamp. Los campos propios de cada fuente que no
# encajan en ECS quedan bajo "extra", sin perderse.


def _ecs_event(
    category: str,
    severity: str,
    description: str,
    *,
    source_ip: str | None = None,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "@timestamp": utcnow().isoformat(),
        "event": {"category": category, "severity": severity},
        "source": {"ip": source_ip},
        "rule": {"description": description},
        "extra": extra or {},
    }


def simulate_connector_test(connector_type: str, base_url: str) -> dict[str, object]:
    connector = connector_type.lower()
    if connector == "pfsense":
        events = [
            _ecs_event("network_traffic", "low", "Estado del enlace WAN", extra={"uptime_status": "up"}),
            _ecs_event("network_traffic", "low", "Sesiones VPN activas", extra={"active_vpn_sessions": 12, "traffic_total_gb": 128}),
        ]
        return {
            "reachable": True,
            "message": f"pfSense endpoint reachable at {base_url}",
            "devices": [
                {
                    "hostname": "pfsense-main",
                    "vendor": "pfSense",
                    "model": "Virtual Appliance",
                    "ip_address": "10.0.0.1",
                    "device_type": "firewall",
                    "status": "healthy",
                }
            ],
            "snapshot": {
                "snapshot_type": "traffic_summary",
                "raw_payload": '{"wan_status":"up","vpn_sessions":12,"traffic_gb":128}',
                "normalized_payload": json.dumps({"events": events}),
            },
        }

    if connector == "fortigate":
        events = [
            _ecs_event("intrusion_detection", "high", "IPS bloqueó tráfico malicioso", source_ip="203.0.113.45", extra={"threat_events": 5, "blocked_intrusions": 3}),
            _ecs_event("network_traffic", "medium", "Estado del enlace WAN degradado", extra={"uptime_status": "degraded"}),
        ]
        return {
            "reachable": True,
            "message": f"FortiGate endpoint reachable at {base_url}",
            "devices": [
                {
                    "hostname": "fortigate-branch-01",
                    "vendor": "FortiGate",
                    "model": "FortiGate VM",
                    "ip_address": "10.0.10.1",
                    "device_type": "firewall",
                    "status": "warning",
                }
            ],
            "snapshot": {
                "snapshot_type": "security_summary",
                "raw_payload": '{"threat_events":5,"ips_blocks":3,"wan_status":"degraded"}',
                "normalized_payload": json.dumps({"events": events}),
            },
        }

    if connector == "wazuh":
        events = [
            _ecs_event("authentication", "critical", "Fuerza bruta SSH detectada (múltiples intentos fallidos)", source_ip="198.51.100.23", extra={"rule_id": "5712", "attempts": 14}),
            _ecs_event("malware", "high", "Firma de malware detectada por syscheck", source_ip="10.0.20.5", extra={"rule_id": "554", "agent": "wazuh-agent-05"}),
            _ecs_event("intrusion_detection", "medium", "Escaneo de puertos detectado", source_ip="192.0.2.77", extra={"rule_id": "40101"}),
        ]
        return {
            "reachable": True,
            "message": f"Wazuh Manager API reachable at {base_url}",
            "devices": [
                {
                    "hostname": "wazuh-manager",
                    "vendor": "Wazuh",
                    "model": "SIEM Manager",
                    "ip_address": "10.0.30.1",
                    "device_type": "server",
                    "status": "healthy",
                }
            ],
            "snapshot": {
                "snapshot_type": "security_alerts",
                "raw_payload": '{"alerts":[{"rule":{"id":"5712","level":10},"agent":{"name":"wazuh-agent-05"}}]}',
                "normalized_payload": json.dumps({"events": events}),
            },
        }

    return {
        "reachable": False,
        "message": f"Connector {connector_type} is not supported yet",
        "devices": [],
        "snapshot": {
            "snapshot_type": "unsupported",
            "raw_payload": "{}",
            "normalized_payload": json.dumps({"events": []}),
            "created_at": utcnow().isoformat(),
        },
    }
