"""Deja la base con un solo administrador y sin datos de demostración.

Para cuando se pasa de «probando con datos de ejemplo» a «esto es mi
sistema». Borra los clientes, proyectos, riesgos y demás inventados, y deja
una sola cuenta.

    PYTHONPATH=. python scripts/limpiar_datos_demo.py \\
        --nombre "Tu Nombre" --correo tu@correo.com

Sin `--si`, solo enseña lo que haría y no toca nada.

## Qué se borra y qué se queda

La diferencia no es «lo viejo» y «lo nuevo»: es **datos de negocio
inventados** frente a **catálogos de referencia que hacen que la aplicación
sirva de algo**.

Borrar los 93 controles de ISO 27001 o las 12 reglas de hardening dejaría un
sistema vacío que hay que rellenar a mano antes de poder usarlo. Eso no es
limpiar, es romper.

## Antes de ejecutarlo

**Haz un respaldo y compruébalo.** Esto no se puede deshacer:

    docker logs ninjasec-respaldos --tail 5

El procedimiento de restauración está en `PY-MK/infra/respaldos/README.md`.
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.db.models.enums import RoleCode, UserStatus
from app.db.models.organization import Organization
from app.db.models.role import Role
from app.db.models.user import User
from app.db.session import SessionLocal


# Datos de negocio inventados. Se vacían.
#
# Van todas en un solo TRUNCATE y SIN CASCADE a propósito: así, si falta
# alguna que otra referencia, PostgreSQL falla y lo dice, en vez de llevarse
# por delante en silencio una tabla que queríamos conservar.
TABLAS_A_VACIAR = [
    # Clientes y lo que cuelga de ellos
    "client_control_status",
    "client_profiles",
    "client_sites",
    "client_contacts",
    "client_services",
    "clients",
    # Proyectos
    "project_requirements",
    "project_members",
    "project_docs",
    "project_tasks",
    "projects",
    # Dispositivos e integraciones
    "device_connections",
    "device_configs",
    "devices",
    "collection_snapshots",
    "integrations",
    "catalog_device_summaries",
    "catalog_device_links",
    # Revisiones, riesgos y auditorías
    "review_findings",
    "security_reviews",
    "risk_vulnerabilities",
    "risk_threats",
    "risk_assets",
    "risks",
    "audits",
    "netdoctor_issues",
    "reports",
    # Comercial y talento
    "leads",
    "service_requests",
    "services",
    "application_events",
    "application_attachments",
    "application_assignments",
    "job_applications",
    "collaborator_profiles",
    "user_certifications",
    "user_skills",
    # Soporte
    "support_ticket_events",
    "ticket_links",
    "support_tickets",
    # Arquitectura empresarial
    "architecture_relationships",
    "architecture_elements",
    "architecture_models",
    # Registro
    "audit_logs",
    "alerts",
    "approvals",
    "notifications",
]

# Catálogos y referencia. NO se tocan: sin ellos la aplicación no sirve.
SE_CONSERVAN = [
    "organizations", "roles", "users (solo el administrador)",
    "study_plans", "study_modules  (planes de estudio)",
    "compliance_frameworks", "compliance_controls  (ISO 27001)",
    "hardening_rules", "threats", "vulnerabilities",
    "catalog_devices", "skills", "doc_types", "project_types", "areas",
    "products", "alembic_version",
]


def tablas_existentes(db: Session, candidatas: list[str]) -> list[str]:
    """Filtra a las que de verdad existen en el esquema.

    La lista se escribe a mano y el esquema cambia. Truncar una tabla
    inexistente aborta la transacción entera, así que se comprueba antes.
    """
    presentes = set(
        db.scalars(
            text(
                "select table_name from information_schema.tables "
                "where table_schema = 'public' and table_type = 'BASE TABLE'"
            )
        )
    )
    return [t for t in candidatas if t in presentes]


TABLAS_INTOCABLES = {
    "users", "organizations", "roles", "alembic_version",
    "study_plans", "study_modules", "study_enrollments", "study_progress",
    "compliance_frameworks", "compliance_controls", "hardening_rules",
    "threats", "vulnerabilities", "catalog_devices", "skills",
    "doc_types", "project_types", "areas", "products",
}


def cerrar_dependencias(db: Session, semilla: list[str]) -> list[str]:
    """Anade las tablas que referencian a las de la lista, en cascada.

    TRUNCATE sin CASCADE falla si alguien referencia una de las tablas, y
    eso es LO QUE QUEREMOS: que avise en vez de llevarse por delante en
    silencio algo que no estaba en la lista.

    Pero la lista se escribe a mano y el esquema crece. En la primera
    ejecucion faltaban seis tablas -- project_recommendations,
    review_attachments, application_notes y tres mas -- que nadie habia
    anotado. En vez de pegarlas a mano y volver a romperse dentro de dos
    modulos, se calculan.

    Si el cierre arrastra una tabla intocable, aborta: significa que la
    semilla incluye algo de lo que cuelga el catalogo, y eso es un error de
    la lista, no algo que se deba borrar.
    """
    aristas = db.execute(
        text(
            """
            select distinct tc.table_name as hija, ccu.table_name as padre
            from information_schema.table_constraints tc
            join information_schema.constraint_column_usage ccu
              on ccu.constraint_name = tc.constraint_name
             and ccu.table_schema = tc.table_schema
            where tc.constraint_type = 'FOREIGN KEY'
              and tc.table_schema = 'public'
            """
        )
    ).all()

    hijas_de: dict[str, set[str]] = {}
    for hija, padre in aristas:
        if hija != padre:  # las autorreferencias no amplian el conjunto
            hijas_de.setdefault(padre, set()).add(hija)

    conjunto = set(semilla)
    pendientes = list(semilla)
    while pendientes:
        actual = pendientes.pop()
        for hija in hijas_de.get(actual, ()):
            if hija not in conjunto:
                conjunto.add(hija)
                pendientes.append(hija)

    arrastradas = conjunto & TABLAS_INTOCABLES
    if arrastradas:
        raise SystemExit(
            "ABORTADO: el cierre de dependencias arrastra tablas que no se "
            f"deben tocar: {sorted(arrastradas)}.\n"
            "Revisa TABLAS_A_VACIAR: alguna no deberia estar ahi."
        )

    anadidas = sorted(conjunto - set(semilla))
    if anadidas:
        print(f"\nAnadidas por dependencia ({len(anadidas)}):")
        print("  " + ", ".join(anadidas))

    return sorted(conjunto)


def contar(db: Session, tablas: list[str]) -> dict[str, int]:
    return {
        t: db.scalar(text(f'select count(*) from "{t}"')) or 0  # noqa: S608
        for t in tablas
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--nombre", required=True, help="Nombre del administrador")
    p.add_argument("--correo", required=True, help="Correo del administrador")
    p.add_argument(
        "--si",
        action="store_true",
        help="Ejecutar de verdad. Sin esto solo se muestra qué pasaría.",
    )
    args = p.parse_args()

    with SessionLocal() as db:
        objetivo = cerrar_dependencias(
            db, tablas_existentes(db, TABLAS_A_VACIAR)
        )
        antes = contar(db, objetivo)
        con_filas = {t: n for t, n in antes.items() if n}

        usuarios = db.scalars(select(User)).all()

        # Si el correo pedido ya existe, ese se queda. Si no, se RENOMBRA el
        # super_admin que haya, en vez de borrarlo y crear otro: crear uno
        # nuevo lo dejaria con la contrasena vacia y sin forma de entrar --
        # un sistema limpio al que no puedes acceder no sirve de nada.
        # Renombrando, la clave actual sigue valiendo.
        destinatario = next((u for u in usuarios if u.email == args.correo), None)
        if destinatario is None:
            destinatario = next(
                (u for u in usuarios if u.role_code == RoleCode.SUPER_ADMIN), None
            )
        a_borrar = [u for u in usuarios if u is not destinatario]

        print("\nSE VACIAN:")
        if con_filas:
            for t, n in sorted(con_filas.items(), key=lambda x: -x[1]):
                print(f"  {n:6}  {t}")
        else:
            print("  (ya estaban vacías)")
        print(f"\n  Tablas sin filas que también se vacían: "
              f"{len(objetivo) - len(con_filas)}")

        print(f"\nSE BORRAN {len(a_borrar)} USUARIOS:")
        for u in a_borrar:
            print(f"  {u.email}")

        print("\nSE CONSERVAN:")
        for t in SE_CONSERVAN:
            print(f"  {t}")

        print(f"\nEL ADMINISTRADOR QUEDA COMO:")
        print(f"  {args.nombre}  <{args.correo}>")
        if destinatario is None:
            print("  ATENCION: no hay ningun super_admin. Se creara uno SIN")
            print("  contrasena, y habra que fijarla antes de poder entrar.")
        elif destinatario.email != args.correo:
            print(f"  (se renombra {destinatario.email}; su clave sigue valiendo)")

        if not args.si:
            print("\nEnsayo. No se tocó nada. Añade --si para ejecutarlo.\n")
            return 0

        print("\nEjecutando...")

        # Un solo TRUNCATE con todas: PostgreSQL resuelve el orden entre
        # ellas. RESTART IDENTITY para que los ids vuelvan a empezar en 1 y
        # no haya huecos raros en un sistema que arranca de cero.
        lista = ", ".join(f'"{t}"' for t in objetivo)
        db.execute(text(f"TRUNCATE TABLE {lista} RESTART IDENTITY"))  # noqa: S608

        # Los usuarios después: audit_logs referencia users SIN ondelete, y
        # borrar un usuario con auditoría asociada revienta con un 500. Al
        # vaciar audit_logs arriba, esto ya es seguro.
        for u in a_borrar:
            db.delete(u)
        db.flush()

        # El administrador que queda, o se crea si no habia ninguno.
        admin = destinatario
        if admin is None:
            org = db.scalar(select(Organization))
            rol = db.scalar(select(Role).where(Role.code == RoleCode.SUPER_ADMIN.value))
            if not org or not rol:
                print("ERROR: falta la organización o el rol super_admin.")
                db.rollback()
                return 1
            # Se reutiliza el hash del admin anterior si lo había; si no,
            # hay que fijar la clave desde la aplicación.
            print("  Creando el administrador. Define su clave desde la aplicación.")
            admin = User(
                organization_id=org.id,
                role_id=rol.id,
                role_code=RoleCode.SUPER_ADMIN,
                full_name=args.nombre,
                email=args.correo,
                password_hash="",
                status=UserStatus.ACTIVE,
                is_active=True,
            )
            db.add(admin)
        else:
            admin.email = args.correo
            admin.full_name = args.nombre
            admin.role_code = RoleCode.SUPER_ADMIN
            admin.is_active = True
            admin.status = UserStatus.ACTIVE

        db.commit()

        quedan = db.scalar(select(func.count()).select_from(User))
        print(f"\nHecho. Queda {quedan} usuario y los catálogos intactos.\n")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
