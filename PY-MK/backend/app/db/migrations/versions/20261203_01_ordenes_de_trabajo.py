"""Órdenes de trabajo: solicitudes, cotizaciones, ítems, órdenes e historial (36-P-01).

Cinco tablas nuevas; no toca ninguna existente. Bajar borra solo esas cinco.

Revision ID: 20261203_01
Revises: 20261202_01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261203_01"
down_revision: str | None = "20261202_01"
branch_labels = None
depends_on = None

_REQUEST = ("new", "reviewing", "quoted", "converted", "discarded")
_QUOTE = ("draft", "sent", "approved", "rejected", "expired", "superseded")
_ORDER = (
    "pending_assignment",
    "assigned",
    "in_progress",
    "on_hold",
    "completed",
    "accepted",
    "closed",
    "cancelled",
)


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def _org() -> sa.Column:
    return sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False)


def _stamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "work_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("client_sites.id", ondelete="SET NULL"), nullable=True),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        *_stamps(),
        sa.CheckConstraint(_in("status", _REQUEST), name="status"),
        sa.CheckConstraint(_in("priority", ("low", "medium", "high", "critical")), name="priority"),
    )
    op.create_index("ix_work_requests_client_id", "work_requests", ["client_id"])
    op.create_index("ix_work_requests_org_status", "work_requests", ["organization_id", "status"])

    op.create_table(
        "quotes",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("work_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.String(20), nullable=False),
        sa.Column("version", sa.SmallInteger(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("decided_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("decision_note", sa.String(1000), nullable=True),
        *_stamps(),
        sa.CheckConstraint(_in("status", _QUOTE), name="status"),
        sa.CheckConstraint("version >= 1", name="version"),
        sa.CheckConstraint("subtotal >= 0 AND tax >= 0", name="amounts"),
        sa.CheckConstraint("total = subtotal + tax", name="total"),
        sa.UniqueConstraint("request_id", "version", name="uq_quotes_request_version"),
    )
    op.create_index(
        "uq_quotes_request_open",
        "quotes",
        ["request_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('draft', 'sent')"),
        sqlite_where=sa.text("status IN ('draft', 'sent')"),
    )
    op.create_index("ix_quotes_org_status", "quotes", ["organization_id", "status"])

    op.create_table(
        "quote_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("quote_id", sa.Integer(), sa.ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(12), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
        sa.CheckConstraint(_in("kind", ("labor", "material", "travel")), name="kind"),
        sa.CheckConstraint("quantity > 0", name="quantity"),
        sa.CheckConstraint("unit_price >= 0", name="unit_price"),
    )
    op.create_index("ix_quote_items_quote_id", "quote_items", ["quote_id"])

    op.create_table(
        "work_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("quote_id", sa.Integer(), sa.ForeignKey("quotes.id"), nullable=False, unique=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("client_sites.id", ondelete="SET NULL"), nullable=True),
        sa.Column("number", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("assigned_to", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("completion_note", sa.Text(), nullable=True),
        *_stamps(),
        sa.CheckConstraint(_in("status", _ORDER), name="status"),
        sa.CheckConstraint(
            "assigned_to IS NOT NULL OR status IN ('pending_assignment', 'cancelled')",
            name="assignee",
        ),
        sa.UniqueConstraint("organization_id", "number", name="uq_work_orders_org_number"),
    )
    op.create_index("ix_work_orders_client_id", "work_orders", ["client_id"])
    op.create_index("ix_work_orders_org_assignee", "work_orders", ["organization_id", "assigned_to", "status"])

    op.create_table(
        "work_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("work_requests.id", ondelete="CASCADE"), nullable=True),
        sa.Column("quote_id", sa.Integer(), sa.ForeignKey("quotes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=True),
        sa.Column("from_status", sa.String(20), nullable=True),
        sa.Column("to_status", sa.String(20), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("note", sa.String(1000), nullable=True),
        sa.Column("internal", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "(CASE WHEN request_id IS NULL THEN 0 ELSE 1 END)"
            " + (CASE WHEN quote_id IS NULL THEN 0 ELSE 1 END)"
            " + (CASE WHEN work_order_id IS NULL THEN 0 ELSE 1 END) = 1",
            name="one_entity",
        ),
    )
    op.create_index("ix_work_events_organization_id", "work_events", ["organization_id"])
    op.create_index("ix_work_events_request", "work_events", ["request_id"])
    op.create_index("ix_work_events_quote", "work_events", ["quote_id"])
    op.create_index("ix_work_events_work_order", "work_events", ["work_order_id"])


def downgrade() -> None:
    op.drop_table("work_events")
    op.drop_table("work_orders")
    op.drop_table("quote_items")
    op.drop_index("uq_quotes_request_open", table_name="quotes")
    op.drop_table("quotes")
    op.drop_table("work_requests")
