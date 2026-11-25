"""Menus de la aplicacion: que opciones existen y a quien se pueden mostrar.

Hay tres superficies, y cada una tiene sus propias audiencias:

    public   la barra del sitio web.      Audiencia: visitor
    staff    el menu lateral del panel.   super_admin, admin, collaborator
    portal   el menu lateral del portal.  client, collaborator, admin, super_admin

Cada opcion se identifica por su RUTA (`clave`), que es lo que el frontend ya
tiene, asi que no hace falta mantener ids aparte.

## Lo que esto controla y lo que NO

Controla **que se muestra**. No es un permiso. Quien conozca la direccion de
una pagina la abre igual si el backend no se lo impide; lo que lo impide es
`require_roles` en cada endpoint.

Por eso cada opcion declara `permitidas`: los roles a los que el backend ya
deja usar esa pantalla. El editor solo puede **mostrar u ocultar dentro de
ese conjunto**. Mostrarle "Leads" a un colaborador no serviria de nada: veria
el enlace y recibiria un 403 al pulsarlo. Un menu que lleva a errores es peor
que uno que no muestra la opcion.

Las listas por defecto replican lo que el frontend tenia escrito en el codigo
(`sidebar.tsx`, `portal-sidebar.tsx`, `site-header.tsx`), de modo que sin
ningun cambio guardado nadie nota nada.
"""

from __future__ import annotations

from dataclasses import dataclass

# Superficie -> audiencias que tiene.
SUPERFICIES: dict[str, tuple[str, ...]] = {
    "public": ("visitor",),
    "staff": ("super_admin", "admin", "collaborator"),
    # El portal es del cliente: PortalGuard deja entrar solo a ese rol.
    "portal": ("client",),
}

_STAFF = ("super_admin", "admin", "collaborator")
_ADMINS = ("super_admin", "admin")


@dataclass(frozen=True)
class Opcion:
    superficie: str
    clave: str  # la ruta
    etiqueta: str
    grupo: str
    # Roles que el backend deja usar esa pantalla. Por defecto se muestra a
    # todos ellos.
    permitidas: tuple[str, ...]
    # Audiencias a las que NO se puede ocultar: ocultarlas dejaria a alguien
    # sin forma de entrar o de volver a arreglarlo.
    obligatoria_para: tuple[str, ...] = ()
    # Capsula de funcionalidad de la que depende. Si esta apagada, la opcion
    # no se muestra a nadie, diga lo que diga esta configuracion.
    capsula: str | None = None


def _pub(clave: str, etiqueta: str, *, fija: bool = False) -> Opcion:
    return Opcion(
        "public", clave, etiqueta, "Sitio web", ("visitor",),
        obligatoria_para=("visitor",) if fija else (),
    )


def _staff(clave, etiqueta, grupo, permitidas=_STAFF, *, fija=(), capsula=None) -> Opcion:
    return Opcion("staff", clave, etiqueta, grupo, permitidas, tuple(fija), capsula)


def _portal(clave, etiqueta, permitidas) -> Opcion:
    return Opcion("portal", clave, etiqueta, "Portal", tuple(permitidas))


OPCIONES: tuple[Opcion, ...] = (
    # --- Sitio web ----------------------------------------------------------
    _pub("/", "Inicio"),
    _pub("/nosotros", "Nosotros"),
    _pub("/servicios", "Servicios"),
    _pub("/proyectos", "Proyectos"),
    # Describe conectores por API: va con la capsula de telemetria.
    Opcion("public", "/solucion", "Solución", "Sitio web", ("visitor",), capsula="telemetria"),
    _pub("/contacto", "Contacto"),
    _pub("/agenda-demo", "Agenda reunión"),
    _pub("/colabora", "Colabora"),
    # Sin Login nadie podria entrar al panel para deshacer el cambio.
    _pub("/login", "Login", fija=True),
    # --- Panel del equipo ---------------------------------------------------
    _staff("/dashboard", "Dashboard", "Inicio", _ADMINS),
    _staff("/dashboard/projects", "Proyectos", "Operación"),
    _staff("/dashboard/integrations", "Integraciones", "Herramientas Ninja Sec", capsula="telemetria"),
    _staff("/dashboard/devices", "Dispositivos", "Herramientas Ninja Sec"),
    _staff("/dashboard/security-reviews", "Revisiones", "Operación"),
    _staff("/dashboard/risks", "Riesgos", "Herramientas Ninja Sec"),
    _staff("/dashboard/hardening", "Hardening", "Herramientas Ninja Sec", capsula="telemetria"),
    _staff("/dashboard/vulnerabilities", "Vulnerabilidades", "Herramientas Ninja Sec"),
    _staff("/dashboard/sgsi", "Guía SGSI", "Herramientas Ninja Sec"),
    _staff("/dashboard/netdoctor", "NetDoctor", "Herramientas Ninja Sec"),
    _staff("/dashboard/catalog-devices", "Catálogo de equipos", "Herramientas Ninja Sec"),
    _staff("/dashboard/soc-report", "Informe SOC", "Herramientas Ninja Sec", capsula="telemetria"),
    _staff("/dashboard/ninja-dev", "Guía Ninja Dev", "Herramientas Ninja Dev"),
    _staff("/dashboard/mis-tareas", "Mis tareas", "Operación"),
    _staff("/dashboard/support-tickets", "Tickets", "Operación"),
    _staff("/dashboard/work-windows", "Ventanas de trabajo", "Operación"),
    _staff("/dashboard/clients", "Clientes", "Comercial"),
    _staff("/dashboard/collaborators", "Colaboradores", "Equipo"),
    _staff("/dashboard/leads", "Leads", "Comercial", _ADMINS),
    _staff("/dashboard/services", "Servicios", "Comercial", _ADMINS),
    _staff("/dashboard/formacion", "Formación", "Equipo"),
    _staff("/dashboard/users", "Usuarios", "Equipo", _ADMINS),
    _staff("/dashboard/applications", "Postulaciones", "Equipo", _ADMINS),
    _staff("/dashboard/reports", "Reportes", "Control", _ADMINS),
    _staff("/dashboard/audit", "Auditoría", "Control", ("super_admin",)),
    # Aqui vive el editor de menus: sin esta, el super_admin se quedaria sin
    # forma de volver a mostrar lo que ocultó.
    _staff("/dashboard/settings", "Configuración", "Control", _ADMINS,
           fija=("super_admin",)),
    # --- Portal -------------------------------------------------------------
    _portal("/portal", "Inicio", ("client",)),
    _portal("/portal/projects", "Proyectos", ("client",)),
    _portal("/portal/inventory", "Inventario", ("client",)),
    _portal("/portal/documents", "Documentos", ("client",)),
    _portal("/portal/tickets", "Tickets", ("client",)),
    _portal("/portal/work-windows", "Ventanas de trabajo", ("client",)),
    _portal("/portal/services", "Servicios", ("client",)),
    _portal("/portal/profile", "Perfil", ("client",)),
)

_POR_CLAVE: dict[tuple[str, str], Opcion] = {(o.superficie, o.clave): o for o in OPCIONES}


def opcion(superficie: str, clave: str) -> Opcion | None:
    return _POR_CLAVE.get((superficie, clave))


def opciones_de(superficie: str) -> list[Opcion]:
    return [o for o in OPCIONES if o.superficie == superficie]


def visible_por_defecto(o: Opcion, audiencia: str) -> bool:
    return audiencia in o.permitidas


def audiencias_de(o: Opcion) -> tuple[str, ...]:
    """Audiencias de la superficie a las que esta opcion se puede mostrar."""
    return tuple(a for a in SUPERFICIES[o.superficie] if a in o.permitidas)
