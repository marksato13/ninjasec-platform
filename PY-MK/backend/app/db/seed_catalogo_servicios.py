"""Catálogo de servicios de NinjaSec: infraestructura, nube, seguridad y desarrollo.

Es **contenido**, no datos de prueba, y por eso vive aparte de `seed.py`: se
puede volver a ejecutar cuando el catálogo cambie sin arrastrar clientes ni
usuarios de demostración.

    PYTHONPATH=. python -m app.db.seed_catalogo_servicios

Idempotente: busca por `(organization_id, slug)` y actualiza en vez de duplicar.

## Qué hay y qué NO hay

Sale del catálogo comercial, que separa lo que está probado de lo que todavía
no se vende. Por eso **no** hay un servicio de «conectarnos a tu firewall por
API», ni de informe SOC, ni de hardening automatizado: los conectores son
simulados. Y los **precios no están aquí**: son una propuesta sin validar y
viven en el repositorio privado. Cada servicio se muestra «A cotizar».

La nube (AWS) sí está, porque es una línea que NinjaSec quiere ofrecer, pero
con un texto de lo que se puede hacer, no de lo ya entregado: no tiene
todavía el respaldo de evidencia que tienen los de redes.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.area import Area
from app.db.models.organization import Organization
from app.db.models.project_type import ProjectType
from app.db.models.service import Service

PRECIO = "A cotizar"

# (slug, titulo, categoria, area, tipo_de_proyecto, resumen, descripcion)
SERVICIOS: list[dict[str, str]] = [
    # --- Infraestructura y redes -------------------------------------------
    {
        "slug": "diagnostico-infraestructura",
        "title": "Diagnóstico de infraestructura",
        "category": "infraestructura",
        "area": "network",
        "tipo": "consulting",
        "summary": "Revisión de solo lectura de tu red y tus equipos: qué tienes, dónde estás débil y qué corregir primero.",
        "description": (
            "Revisamos tu red y tus equipos sin modificar nada. Entregamos un informe de hallazgos, "
            "un diagrama de tu red actual y una lista de prioridades. Suele ser el primer paso, "
            "porque abre la conversación con datos y no con promesas."
        ),
    },
    {
        "slug": "documentacion-tecnica",
        "title": "Documentación técnica y diagramas",
        "category": "infraestructura",
        "area": "it-management",
        "tipo": "consulting",
        "summary": "Topología actualizada, inventario de activos y procedimientos, para auditorías y licitaciones.",
        "description": (
            "Dejamos ordenado lo que hoy está en la cabeza de una persona: topología actualizada, "
            "inventario de activos, procedimientos operativos y matriz de pruebas. Pensado para "
            "cuando llegue un auditor, un banco o una licitación."
        ),
    },
    {
        "slug": "firewall-segmentacion",
        "title": "Firewall perimetral y segmentación de red",
        "category": "infraestructura",
        "area": "network-security",
        "tipo": "implementation",
        "summary": "Firewall, VLANs por zona, VPN y una vuelta atrás probada. Fortinet, Cisco y migración desde MikroTik.",
        "description": (
            "Firewall configurado, VLANs por zona, reglas, VPN, documento de migración y diagrama. "
            "Trabajamos con Fortinet (FortiGate) y Cisco, y migramos desde MikroTik. Se hace en "
            "ventana nocturna con vuelta atrás probada. No incluye el equipo."
        ),
    },
    {
        "slug": "monitoreo-alertas",
        "title": "Monitoreo y alertas",
        "category": "infraestructura",
        "area": "network",
        "tipo": "support",
        "summary": "Vigilamos tus servidores y equipos y te avisamos antes de que llame un cliente.",
        "description": (
            "Servidor de monitoreo, agentes y plantillas, con alertas a Telegram o correo e informe "
            "mensual. Se pone en marcha en una o dos semanas y se acompaña con horas de soporte "
            "mensuales, sin permanencia."
        ),
    },
    # --- Nube ----------------------------------------------------------------
    {
        "slug": "aws-diseno-despliegue",
        "title": "Diseño y despliegue en AWS",
        "category": "nube",
        "area": "devops",
        "tipo": "implementation",
        "summary": "Servidores, redes privadas, copias de seguridad y seguridad básica para tus aplicaciones en AWS.",
        "description": (
            "Diseñamos y desplegamos tu infraestructura en AWS con la misma disciplina que una red "
            "física: redes privadas separadas, acceso mínimo necesario, copias de seguridad "
            "probadas y costos bajo control."
        ),
    },
    {
        "slug": "aws-conexion-red",
        "title": "Conectar tu red con la nube",
        "category": "nube",
        "area": "network",
        "tipo": "implementation",
        "summary": "VPN entre tu oficina y AWS, definiendo qué se ve desde dónde.",
        "description": (
            "Unimos tu oficina con AWS mediante VPN y definimos qué se ve desde dónde, para que la "
            "nube no sea una puerta abierta a tu red interna."
        ),
    },
    # --- Ciberseguridad ------------------------------------------------------
    {
        "slug": "auditoria-iso-27002",
        "title": "Auditoría de seguridad ISO/IEC 27002",
        "category": "seguridad",
        "area": "compliance-grc",
        "tipo": "consulting",
        "summary": "Evaluación contra los controles del estándar, con hallazgos por riesgo y plan de corrección.",
        "description": (
            "Informe con hallazgos, evidencia por control, clasificación por riesgo y un plan de "
            "remediación priorizado. Es de solo lectura: no modifica nada de tu entorno."
        ),
    },
    {
        "slug": "vulnerabilidades-priorizadas",
        "title": "Inventario de vulnerabilidades priorizadas",
        "category": "seguridad",
        "area": "cybersecurity",
        "tipo": "consulting",
        "summary": "No 400 fallos: los pocos que de verdad pueden explotarse, para empezar por ahí.",
        "description": (
            "Inventario de tus activos y de sus vulnerabilidades ordenadas por la probabilidad real "
            "de explotación, no solo por severidad teórica. El inventario de equipos se carga a "
            "partir de lo que tú nos indicas: no descubrimos tu red por nuestra cuenta."
        ),
    },
    # --- Desarrollo ----------------------------------------------------------
    {
        "slug": "sistemas-a-medida",
        "title": "Sistemas a medida",
        "category": "desarrollo",
        "area": "development",
        "tipo": "implementation",
        "summary": "Aplicaciones web, sistemas internos y MVPs, con backend, base de datos y despliegue.",
        "description": (
            "Desarrollamos aplicaciones web, sistemas internos y MVPs completos: backend, base de "
            "datos, interfaz y despliegue. Definimos contigo el alcance, los tiempos y los "
            "entregables antes de empezar."
        ),
    },
    {
        "slug": "apis-integraciones",
        "title": "APIs e integraciones",
        "category": "desarrollo",
        "area": "development",
        "tipo": "implementation",
        "summary": "Conectamos tus sistemas entre sí para que los datos dejen de copiarse a mano.",
        "description": (
            "Construimos APIs e integraciones entre los sistemas que ya usas, para que los datos "
            "viajen solos de uno a otro."
        ),
    },
    {
        "slug": "automatizacion-procesos",
        "title": "Automatización de procesos",
        "category": "desarrollo",
        "area": "devops",
        "tipo": "implementation",
        "summary": "Scripts y flujos que eliminan el trabajo repetitivo de tu equipo.",
        "description": (
            "Identificamos las tareas repetitivas de tu equipo y las automatizamos con scripts y "
            "flujos, con registro de lo que hacen."
        ),
    },
]


def sembrar_catalogo_servicios(db: Session, organization_id: int | None = None) -> int:
    """Crea o actualiza el catálogo. Devuelve cuántos servicios tocó."""
    if organization_id is None:
        organizacion = db.scalar(
            select(Organization).where(Organization.slug == "ninjasec-internal")
        )
        if not organizacion:
            raise RuntimeError(
                "No existe la organización 'ninjasec-internal'. "
                "Ejecuta primero el seed principal."
            )
        organization_id = organizacion.id

    areas = {a.slug: a for a in db.scalars(select(Area)).all()}
    tipos = {t.slug: t for t in db.scalars(select(ProjectType)).all()}

    tocados = 0
    for datos in SERVICIOS:
        servicio = db.scalar(
            select(Service).where(
                Service.organization_id == organization_id, Service.slug == datos["slug"]
            )
        )
        if servicio is None:
            servicio = Service(organization_id=organization_id, slug=datos["slug"])
            db.add(servicio)
        area = areas.get(datos["area"])
        tipo = tipos.get(datos["tipo"])
        servicio.title = datos["title"]
        servicio.category = datos["category"]
        servicio.summary = datos["summary"]
        servicio.description = datos["description"]
        servicio.area_id = area.id if area else None
        servicio.project_type_id = tipo.id if tipo else None
        servicio.price_label = PRECIO
        servicio.is_public = True
        servicio.active = True
        tocados += 1

    db.commit()
    return tocados


if __name__ == "__main__":  # pragma: no cover
    from app.db.session import SessionLocal

    with SessionLocal() as sesion:
        print(f"Servicios sembrados o actualizados: {sembrar_catalogo_servicios(sesion)}")
