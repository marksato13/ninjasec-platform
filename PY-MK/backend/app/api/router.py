from fastapi import APIRouter

from app.modules.alerts.routers.router import router as alerts_router
from app.modules.audit.routers.router import router as audit_router
from app.modules.architecture.router import router as architecture_router
from app.modules.auth.routers.router import router as auth_router
from app.modules.dashboard.routers.router import router as dashboard_router
from app.modules.clients.routers.router import router as clients_router
from app.modules.clients.routers.sites import router as client_sites_router
from app.modules.clients.routers.contacts import router as client_contacts_router
from app.modules.clients.routers.client_services import router as client_services_router
from app.modules.collaborators.routers.router import router as collaborators_router
from app.modules.collection.routers.router import router as collection_router
from app.modules.devices.routers.router import router as devices_router
from app.modules.devices.routers.connections import router as device_connections_router
from app.modules.devices.routers.configs import router as device_configs_router
from app.modules.catalogs.routers.router import router as catalogs_router
from app.modules.device_catalog.routers.router import router as device_catalog_router
from app.modules.compliance.routers.router import router as compliance_router
from app.modules.audits.routers.router import router as audits_router
from app.modules.docs.routers.router import router as docs_router
from app.modules.integrations.routers.router import router as integrations_router
from app.modules.leads.routers.router import router as leads_router
from app.modules.organizations.routers.router import router as organizations_router
from app.modules.projects.routers.router import router as projects_router
from app.modules.projects.routers.extras import router as project_extras_router
from app.modules.projects.routers.tasks import router as project_tasks_router
from app.modules.security_reviews.routers.router import router as security_reviews_router
from app.modules.skills.routers.router import router as skills_router
from app.modules.recruitment.routers.router import router as recruitment_router
from app.modules.reports.routers.router import router as reports_router
from app.modules.risks.router import router as risks_router
from app.modules.risk_scoring.routers.router import router as risk_scoring_router
from app.modules.hardening.routers.router import router as hardening_router
from app.modules.vulnerability_inventory.routers.router import router as vulnerability_inventory_router
from app.modules.netdoctor.routers.router import router as netdoctor_router
from app.modules.health_score.routers.router import router as health_score_router
from app.modules.services.routers.router import router as services_router
from app.modules.support_tickets.routers.router import router as support_tickets_router
from app.modules.work_windows.routers.router import router as work_windows_router
from app.modules.users.routers.router import router as users_router
from app.modules.navigation.router import router as navigation_router
from app.modules.study.router import router as study_router
from app.modules.tracking.router import router as tracking_router
from app.modules.certifications.routers.router import router as certifications_router

from app.core.config import settings
from app.core.features import inventario, rutas_apagadas

_RUTAS_APAGADAS = frozenset(rutas_apagadas(settings.capsulas_activas))

api_router = APIRouter()


def _registrar(router) -> None:
    """Incluye un router salvo que su cápsula esté apagada.

    Apagar = NO REGISTRAR. La ruta deja de existir y el 404 es el natural de
    FastAPI, no uno fabricado: ni aparece en /openapi.json, ni en /docs, ni
    revela que hay algo detrás.

    Esa es la diferencia con esconder el menú, que es el error clásico: la
    ruta sigue ahí y cualquiera que teclee la URL entra.

    El criterio y los límites estan en
    DOCUMENTOS/ESTRATEGIA/10-MODULOS-ACTIVABLES.md.
    """
    prefijo = getattr(router, "prefix", "") or ""
    if prefijo and prefijo in _RUTAS_APAGADAS:
        return
    api_router.include_router(router)


_registrar(auth_router)
_registrar(dashboard_router)
_registrar(organizations_router)
_registrar(users_router)
_registrar(navigation_router)
_registrar(study_router)
_registrar(tracking_router)
_registrar(clients_router)
_registrar(client_sites_router)
_registrar(client_contacts_router)
_registrar(client_services_router)
_registrar(collaborators_router)
_registrar(devices_router)
_registrar(device_connections_router)
_registrar(device_configs_router)
_registrar(catalogs_router)
_registrar(device_catalog_router)
_registrar(compliance_router)
_registrar(audits_router)
_registrar(skills_router)
_registrar(certifications_router)
_registrar(projects_router)
_registrar(project_extras_router)
_registrar(project_tasks_router)
_registrar(services_router)
_registrar(leads_router)
_registrar(recruitment_router)
_registrar(integrations_router)
_registrar(collection_router)
_registrar(security_reviews_router)
_registrar(support_tickets_router)
_registrar(work_windows_router)
_registrar(alerts_router)
_registrar(reports_router)
_registrar(risks_router)
_registrar(risk_scoring_router)
_registrar(hardening_router)
_registrar(vulnerability_inventory_router)
_registrar(netdoctor_router)
_registrar(health_score_router)
_registrar(docs_router)
_registrar(audit_router)
_registrar(architecture_router)


@api_router.get("/capsulas", tags=["meta"])
def listar_capsulas() -> dict[str, object]:
    """Que capsulas estan encendidas y por que las demas no.

    El frontend lo consulta para saber que pantallas pintar. No lleva nada
    sensible: son nombres de modulo y de ruta, que ademas estan en el
    repositorio.

    Va sin autenticacion a proposito: el frontend necesita saber que menu
    dibujar antes de que nadie inicie sesion, y la respuesta no dice nada que
    no se pueda leer en el codigo.
    """
    return {"capsulas": inventario(settings.capsulas_activas)}


@api_router.get("/")
def root() -> dict[str, object]:
    return {
        "message": "Welcome to Ninja Tech API",
        "docs": "/docs",
        "modules": [
            "auth",
            "dashboard",
            "organizations",
            "users",
            "clients",
            "client-sites",
            "client-contacts",
            "client-services",
            "collaborators",
            "devices",
            "catalogs",
            "skills",
            "certifications",
            "projects",
            "services",
            "leads",
            "recruitment",
            "integrations",
            "collection",
            "security-reviews",
            "support-tickets",
            "alerts",
            "reports",
            "docs",
            "audit",
        ],
    }
