"""Pruebas de integración para la exportación de registros de auditoría."""

import base64
import io
import re
import zlib

import openpyxl

from app.db.models.audit_log import AuditLog

API = "/api/v1"
EXPORT_LIMIT = 5_000
HEADERS = ("Fecha", "Usuario", "Acción", "Entidad afectada")


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _export(http_client, admin_token: str, export_format: str, **filters):
    return http_client.get(
        f"{API}/audit-logs/export",
        params={"format": export_format, **filters},
        headers=_headers(admin_token),
    )


def _xlsx_rows(response) -> list[tuple]:
    workbook = openpyxl.load_workbook(io.BytesIO(response.content), read_only=True)
    try:
        return list(workbook.active.values)
    finally:
        workbook.close()


def _add_log(db, organization_id: int, **values) -> None:
    db.add(AuditLog(organization_id=organization_id, **values))


def _seed_filtered_events(db, seed_data) -> str:
    """Crea un único evento que satisface los tres filtros disponibles."""
    matching_id = "audit-export-matching-event"
    _add_log(
        db,
        seed_data["org"].id,
        user_id=seed_data["admin"].id,
        action="client.created",
        entity_type="client",
        entity_id=matching_id,
    )
    _add_log(
        db,
        seed_data["org"].id,
        user_id=seed_data["admin"].id,
        action="client.updated",
        entity_type="client",
        entity_id=matching_id,
    )
    _add_log(
        db,
        seed_data["org"].id,
        user_id=seed_data["admin"].id,
        action="client.created",
        entity_type="device",
        entity_id=matching_id,
    )
    _add_log(
        db,
        seed_data["org"].id,
        user_id=seed_data["admin"].id,
        action="client.created",
        entity_type="client",
        entity_id="audit-export-excluded-event",
    )
    db.commit()
    return matching_id


def _pdf_text(pdf: bytes) -> bytes:
    """Extrae los streams de texto comprimidos por ReportLab, sin dependencias extra."""
    streams = re.findall(rb"stream\r?\n(.*?)\r?\n?endstream", pdf, re.DOTALL)
    return b"".join(
        zlib.decompress(base64.a85decode(stream.strip()[:-2]))
        for stream in streams
        if stream.strip().endswith(b"~>")
    )


def test_audit_xlsx_is_valid_and_propagates_every_filter(
    http_client, admin_token, seed_data, db
):
    """El XLSX aplica acción, entidad e ID; conserva las columnas requeridas."""
    matching_id = _seed_filtered_events(db, seed_data)

    filters = {
        "action": "client.created",
        "entity_type": "client",
        "entity_id": matching_id,
    }
    xlsx = _export(http_client, admin_token, "xlsx", **filters)
    assert xlsx.status_code == 200, xlsx.text
    assert xlsx.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert xlsx.headers["x-export-limit"] == str(EXPORT_LIMIT)
    rows = _xlsx_rows(xlsx)
    assert rows[0] == HEADERS
    assert len(rows) == 2
    assert rows[1][0]  # Fecha
    assert rows[1][1:] == (
        "Test Admin",
        "client.created",
        f"client #{matching_id}",
    )


def test_audit_pdf_is_valid_and_propagates_every_filter(
    http_client, admin_token, seed_data, db
):
    """El PDF aplica los mismos filtros y contiene las columnas exportadas."""
    matching_id = _seed_filtered_events(db, seed_data)
    filters = {
        "action": "client.created",
        "entity_type": "client",
        "entity_id": matching_id,
    }

    pdf = _export(http_client, admin_token, "pdf", **filters)
    assert pdf.status_code == 200, pdf.text
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert pdf.headers["x-export-limit"] == str(EXPORT_LIMIT)
    assert pdf.content.startswith(b"%PDF-")
    assert pdf.content.rstrip().endswith(b"%%EOF")
    assert len(pdf.content) > 1_000
    text = _pdf_text(pdf.content)
    for column in (b"Fecha", b"Usuario", b"Acci", b"Entidad afectada"):
        assert column in text
    assert b"client.created" in text
    assert f"client #{matching_id}".encode() in text
    assert b"audit-export-excluded-event" not in text


def test_audit_export_limits_the_number_of_records(http_client, admin_token, seed_data, db):
    """Una exportación masiva conserva el encabezado y no supera el límite seguro."""
    bulk_entity_id = "audit-export-volume-limit"
    db.add_all(
        AuditLog(
            organization_id=seed_data["org"].id,
            user_id=seed_data["admin"].id,
            action="bulk.exported",
            entity_type="bulk",
            entity_id=bulk_entity_id,
        )
        for _ in range(EXPORT_LIMIT + 1)
    )
    db.commit()

    response = _export(
        http_client,
        admin_token,
        "xlsx",
        action="bulk.exported",
        entity_type="bulk",
        entity_id=bulk_entity_id,
    )
    assert response.status_code == 200, response.text
    assert response.headers["x-export-limit"] == str(EXPORT_LIMIT)
    rows = _xlsx_rows(response)
    assert rows[0] == HEADERS
    assert len(rows) == EXPORT_LIMIT + 1
    assert all(row[2] == "bulk.exported" for row in rows[1:])


def test_audit_exports_without_results_are_valid_and_keep_headers(
    http_client, admin_token
):
    """Una consulta vacía sigue entregando archivos descargables con encabezados."""
    filters = {"entity_id": "audit-export-no-results"}

    xlsx = _export(http_client, admin_token, "xlsx", **filters)
    assert xlsx.status_code == 200, xlsx.text
    assert _xlsx_rows(xlsx) == [HEADERS]

    pdf = _export(http_client, admin_token, "pdf", **filters)
    assert pdf.status_code == 200, pdf.text
    assert pdf.content.startswith(b"%PDF-")
    assert pdf.content.rstrip().endswith(b"%%EOF")
