"""Catálogo de skills: las tecnologías, normas y marcos con que trabaja NinjaSec.

Es **contenido**, como `seed_catalogo_servicios.py`: se puede volver a ejecutar
cuando el catálogo crezca.

    PYTHONPATH=. python -m app.db.seed_catalogo_skills

## Las skills son globales, no por organización

El modelo `Skill` no tiene `organization_id` y su `name` es único en toda la
tabla: el catálogo es uno solo para toda la plataforma. Lo que sí es de cada
organización es quién declara qué (`UserSkill`), y eso este seed no lo toca.
Por eso aquí no hay parámetro de organización: no se inventa una columna ni
una migración para tenerlo.

## Idempotente y conservador

- Compara por nombre normalizado (minúsculas, sin tildes, espacios
  colapsados): si ya existe «python» o «PYTHON», no crea «Python».
- Nunca borra ni renombra. Si una skill existente no tiene categoría, se la
  pone; si ya tiene una, la respeta.

Los nombres coinciden con `frontend/src/lib/marcas.ts`, así cada skill
sembrada sale con su logo en Formación.
"""

from __future__ import annotations

import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.skill import Skill

# Categoría (texto que se ve en la UI) -> nombres de skill.
CATALOGO: dict[str, list[str]] = {
    "Redes y equipos": [
        "Cisco", "Cisco Packet Tracer", "FortiGate", "MikroTik", "pfSense", "Ubiquiti UniFi",
        "VLAN", "OSPF", "BGP", "DNS", "DHCP", "IPsec", "OpenVPN", "WireGuard", "nftables",
        "Nginx", "Caddy", "Cloudflare",
    ],
    "Seguridad": [
        "Wazuh", "Suricata", "Snort", "Wireshark", "Nmap", "Splunk", "Keycloak",
        "HashiCorp Vault", "RADIUS", "LDAP", "OWASP",
    ],
    "Sistemas operativos": [
        "Linux", "Ubuntu", "Debian", "Red Hat", "CentOS", "Kali Linux", "Windows Server",
    ],
    "Virtualización y contenedores": [
        "Proxmox", "VMware ESXi", "VirtualBox", "Docker", "Kubernetes", "EVE-NG", "GNS3",
    ],
    "Nube": ["AWS", "Oracle Cloud", "MinIO"],
    "Monitoreo": ["Zabbix", "Grafana", "Prometheus", "Nagios", "Elasticsearch"],
    "Lenguajes": ["Python", "Java", "TypeScript", "JavaScript", "PHP", "R", "Bash", "PowerShell", "SQL"],
    "Frameworks y librerías": [
        "Spring Boot", "Angular", "Flutter", "Node.js", "React", "Next.js", "FastAPI", "Django",
        "SQLAlchemy", "Alembic", "scikit-learn",
    ],
    "Bases de datos": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Firebase"],
    "DevOps": ["Git", "GitHub", "Ansible", "Terraform"],
    "Herramientas": ["Postman", "Jupyter", "draw.io", "Excel", "Visio", "GLPI"],
    "Normas y marcos": [
        "ISO/IEC 27001", "ISO/IEC 27002", "ISO 19011", "NIST CSF", "CIS Controls", "ITIL", "COBIT",
        "MAGERIT", "TOGAF / ArchiMate",
    ],
}


def normalizar(nombre: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", nombre)
    sin_tildes = "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.lower().split())


def sembrar_catalogo_skills(db: Session) -> dict[str, int]:
    """Crea las skills que falten. Devuelve cuántas creó y a cuántas les puso categoría."""
    existentes: dict[str, Skill] = {}
    for skill in db.scalars(select(Skill)).all():
        existentes.setdefault(normalizar(skill.name), skill)

    creadas = categorizadas = 0
    for categoria, nombres in CATALOGO.items():
        for nombre in nombres:
            clave = normalizar(nombre)
            actual = existentes.get(clave)
            if actual is None:
                nueva = Skill(name=nombre, category=categoria, is_active=True)
                db.add(nueva)
                existentes[clave] = nueva
                creadas += 1
            elif not actual.category:
                actual.category = categoria
                categorizadas += 1

    db.commit()
    return {"creadas": creadas, "categorizadas": categorizadas}


if __name__ == "__main__":  # pragma: no cover
    from app.db.session import SessionLocal

    with SessionLocal() as sesion:
        r = sembrar_catalogo_skills(sesion)
        print(f"Skills creadas: {r['creadas']} · con categoría nueva: {r['categorizadas']}")
