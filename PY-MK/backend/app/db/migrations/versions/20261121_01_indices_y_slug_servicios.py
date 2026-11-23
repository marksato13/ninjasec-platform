"""Indices de claves foraneas y unicidad compuesta en services.slug

Dos arreglos de la auditoria de base de datos del 2026-11-21, juntos porque
los dos se vuelven caros en cuanto haya datos reales.

1. `services.slug` tenia `unique=True` de UNA SOLA COLUMNA sobre una tabla
   con `organization_id NOT NULL`. El primer cliente que creara el servicio
   "pentest-web" se quedaba ese slug para toda la plataforma. Es el mismo
   fallo que 20260806_01 corrigio para areas, project_types y products.
   Despues de tener dos organizaciones hay que resolver colisiones reales a
   mano; ahora es gratis.

2. El esquema tenia 8 indices y 100 columnas de clave foranea SIN indice.
   PostgreSQL no los crea solo. Cada JOIN, cada filtro por padre y cada
   ON DELETE era un recorrido completo de la tabla. Con las tablas vacias
   esta migracion tarda milisegundos; sobre una base con datos hay que
   partirla en CREATE INDEX CONCURRENTLY fuera de transaccion.

Se indexan las foraneas que de verdad se consultan -- las que cuelgan de un
padre que se lista, y los organization_id. Quedan fuera a proposito las de
autoria (`created_by`, `verified_by`, `updated_by`): hoy no se filtran por
ellas, y un indice que nadie usa solo encarece las escrituras. Se anadiran
cuando se implemente el `ON DELETE SET NULL` de la politica de borrado, que
si las necesita.

Revision ID: 20261121_01
Revises: 20260810_01
"""

from alembic import op
import sqlalchemy as sa

revision = "20261121_01"
down_revision = "20260810_01"
branch_labels = None
depends_on = None


# (tabla, columnas, nombre). Orden: primero lo que mas crece.
INDICES: list[tuple[str, list[str], str]] = [
    # Tablas que crecen sin techo
    ("audit_logs", ["organization_id", "created_at"], "ix_audit_logs_org_created"),
    ("audit_logs", ["user_id"], "ix_audit_logs_user"),
    ("collection_snapshots", ["integration_id"], "ix_collection_snapshots_integration"),
    ("collection_snapshots", ["device_id"], "ix_collection_snapshots_device"),
    # organization_id sin indice
    ("clients", ["organization_id"], "ix_clients_org"),
    ("users", ["organization_id"], "ix_users_org"),
    ("integrations", ["organization_id"], "ix_integrations_org"),
    ("projects", ["organization_id"], "ix_projects_org"),
    ("reports", ["organization_id"], "ix_reports_org"),
    ("security_reviews", ["organization_id"], "ix_security_reviews_org"),
    ("services", ["organization_id"], "ix_services_org"),
    # Hijos que siempre se listan por su padre
    ("user_skills", ["user_id"], "ix_user_skills_user"),
    ("user_skills", ["skill_id"], "ix_user_skills_skill"),
    ("user_certifications", ["user_id"], "ix_user_certifications_user"),
    ("project_docs", ["project_id"], "ix_project_docs_project"),
    ("project_members", ["project_id"], "ix_project_members_project"),
    ("project_members", ["user_id"], "ix_project_members_user"),
    ("support_ticket_events", ["ticket_id"], "ix_ticket_events_ticket"),
    ("devices", ["integration_id"], "ix_devices_integration"),
    ("devices", ["site_id"], "ix_devices_site"),
    ("leads", ["status"], "ix_leads_status"),
]


def _tablas(bind) -> set[str]:
    return set(sa.inspect(bind).get_table_names())


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # La suite corre sobre SQLite con create_all: no hay nada que migrar.
        return

    inspector = sa.inspect(bind)
    existentes = _tablas(bind)

    # ---------------- 1. Unicidad compuesta en services.slug ----------------
    if "services" in existentes:
        # Se busca la restriccion antigua en el catalogo en vez de asumir su
        # nombre: la tabla pudo nacer de create_all o de la migracion base, y
        # el nombre generado difiere. Mismo criterio que 20260806_01.
        for uq in inspector.get_unique_constraints("services"):
            if uq["column_names"] == ["slug"]:
                op.drop_constraint(uq["name"], "services", type_="unique")

        for idx in inspector.get_indexes("services"):
            if idx.get("unique") and idx["column_names"] == ["slug"]:
                op.drop_index(idx["name"], table_name="services")

        nombres_uq = {u["name"] for u in inspector.get_unique_constraints("services")}
        if "uq_service_org_slug" not in nombres_uq:
            op.create_unique_constraint(
                "uq_service_org_slug", "services", ["organization_id", "slug"]
            )

    # ---------------------------- 2. Indices --------------------------------
    for tabla, columnas, nombre in INDICES:
        if tabla not in existentes:
            # Una tabla que no existe no es un error: el esquema evoluciona y
            # esta migracion debe poder correr sobre bases historicas.
            continue

        cols_tabla = {c["name"] for c in inspector.get_columns(tabla)}
        if not set(columnas).issubset(cols_tabla):
            continue

        ya_estan = {i["name"] for i in inspector.get_indexes(tabla)}
        if nombre in ya_estan:
            continue

        op.create_index(nombre, tabla, columnas)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return

    inspector = sa.inspect(bind)
    existentes = _tablas(bind)

    for tabla, _columnas, nombre in reversed(INDICES):
        if tabla in existentes and nombre in {i["name"] for i in inspector.get_indexes(tabla)}:
            op.drop_index(nombre, table_name=tabla)

    if "services" in existentes:
        nombres_uq = {u["name"] for u in inspector.get_unique_constraints("services")}
        if "uq_service_org_slug" in nombres_uq:
            op.drop_constraint("uq_service_org_slug", "services", type_="unique")

        # Volver a la unicidad global solo es posible si no hay dos
        # organizaciones usando el mismo slug. Si las hay, se falla a
        # proposito en vez de perder datos en silencio -- mismo criterio que
        # el downgrade de 20260806_01.
        duplicados = bind.execute(
            sa.text(
                "SELECT slug FROM services GROUP BY slug HAVING COUNT(*) > 1 LIMIT 5"
            )
        ).fetchall()
        if duplicados:
            raise RuntimeError(
                "No se puede revertir: hay slugs repetidos entre organizaciones "
                f"({', '.join(d[0] for d in duplicados)}). Resuelvelos antes."
            )
        op.create_unique_constraint("uq_services_slug", "services", ["slug"])
