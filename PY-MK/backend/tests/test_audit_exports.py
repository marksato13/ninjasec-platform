import io

import openpyxl

from app.db.models.audit_log import AuditLog

API = "/api/v1"


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_audit_exports_apply_filters_and_generate_valid_files(
    http_client, admin_token, seed_data, db
):
    db.add_all([
        AuditLog(
            organization_id=seed_data["org"].id,
            user_id=seed_data["admin"].id,
            action="client.created",
            entity_type="client",
            entity_id="audit-export-match",
        ),
        AuditLog(
            organization_id=seed_data["org"].id,
            action="device.updated",
            entity_type="device",
            entity_id="audit-export-other",
        ),
    ])
    db.commit()
    params = {
        "action": "client.created",
        "entity_type": "client",
        "entity_id": "audit-export-match",
    }

    xlsx = http_client.get(
        f"{API}/audit-logs/export",
        params={"format": "xlsx", **params},
        headers=_headers(admin_token),
    )
    assert xlsx.status_code == 200, xlsx.text
    assert xlsx.headers["x-export-limit"] == "5000"
    workbook = openpyxl.load_workbook(io.BytesIO(xlsx.content), read_only=True)
    values = list(workbook.active.values)
    assert values[0] == ("Fecha", "Usuario", "Acción", "Entidad afectada")
    assert len(values) == 2
    assert values[1][1:] == ("Test Admin", "client.created", "client #audit-export-match")

    pdf = http_client.get(
        f"{API}/audit-logs/export",
        params={"format": "pdf", **params},
        headers=_headers(admin_token),
    )
    assert pdf.status_code == 200, pdf.text
    assert pdf.content.startswith(b"%PDF-")
    assert pdf.content.rstrip().endswith(b"%%EOF")
    assert len(pdf.content) > 1_000


def test_audit_exports_without_results_keep_headers(http_client, admin_token):
    params = {"entity_id": "does-not-exist"}
    xlsx = http_client.get(
        f"{API}/audit-logs/export",
        params={"format": "xlsx", **params},
        headers=_headers(admin_token),
    )
    workbook = openpyxl.load_workbook(io.BytesIO(xlsx.content), read_only=True)
    assert list(workbook.active.values) == [
        ("Fecha", "Usuario", "Acción", "Entidad afectada")
    ]

    pdf = http_client.get(
        f"{API}/audit-logs/export",
        params={"format": "pdf", **params},
        headers=_headers(admin_token),
    )
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF-")
    assert pdf.content.rstrip().endswith(b"%%EOF")
