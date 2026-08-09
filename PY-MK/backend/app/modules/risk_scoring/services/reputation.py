"""30-P2: clientes de reputación externa de IPs.

Cada función degrada con gracia cuando no hay API key configurada (o si la
fuente real no responde): devuelve un score simulado y determinista (mismo
hash -> mismo score, para que la demo sea consistente) en vez de romper.
Nunca lanza una excepción hacia el llamador.
"""
from __future__ import annotations

import hashlib

import httpx

from app.core.config import settings


def _simulated_score(ip: str, salt: str) -> int:
    digest = hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()
    return int(digest[:2], 16) % 101


def check_abuseipdb(ip: str) -> dict[str, object]:
    if not settings.abuseipdb_api_key:
        return {"source": "abuseipdb", "score": _simulated_score(ip, "abuseipdb"), "category": "simulated"}
    try:
        response = httpx.get(
            "https://api.abuseipdb.com/api/v2/check",
            params={"ipAddress": ip, "maxAgeInDays": 90},
            headers={"Key": settings.abuseipdb_api_key, "Accept": "application/json"},
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json().get("data", {})
        return {"source": "abuseipdb", "score": int(data.get("abuseConfidenceScore", 0)), "category": "real"}
    except (httpx.HTTPError, ValueError, KeyError):
        return {"source": "abuseipdb", "score": _simulated_score(ip, "abuseipdb"), "category": "unreachable_fallback"}


def check_virustotal(ip: str) -> dict[str, object]:
    if not settings.virustotal_api_key:
        return {"source": "virustotal", "score": _simulated_score(ip, "virustotal"), "category": "simulated"}
    try:
        response = httpx.get(
            f"https://www.virustotal.com/api/v3/ip_addresses/{ip}",
            headers={"x-apikey": settings.virustotal_api_key},
            timeout=5.0,
        )
        response.raise_for_status()
        stats = response.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        malicious = int(stats.get("malicious", 0))
        total = sum(stats.values()) or 1
        return {"source": "virustotal", "score": round(100 * malicious / total), "category": "real"}
    except (httpx.HTTPError, ValueError, KeyError):
        return {"source": "virustotal", "score": _simulated_score(ip, "virustotal"), "category": "unreachable_fallback"}


def check_greynoise(ip: str) -> dict[str, object]:
    if not settings.greynoise_api_key:
        return {"source": "greynoise", "score": _simulated_score(ip, "greynoise"), "category": "simulated"}
    try:
        response = httpx.get(
            f"https://api.greynoise.io/v3/community/{ip}",
            headers={"key": settings.greynoise_api_key, "Accept": "application/json"},
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json()
        classification = str(data.get("classification", "unknown"))
        score = {"malicious": 90, "suspicious": 60, "benign": 5, "unknown": 20}.get(classification, 20)
        return {"source": "greynoise", "score": score, "category": "real"}
    except (httpx.HTTPError, ValueError, KeyError):
        return {"source": "greynoise", "score": _simulated_score(ip, "greynoise"), "category": "unreachable_fallback"}


REPUTATION_CHECKERS = (check_abuseipdb, check_virustotal, check_greynoise)
