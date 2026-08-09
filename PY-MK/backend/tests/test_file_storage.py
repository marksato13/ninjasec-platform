from app.db.models.doc_type import DocType
from app.db.models.enums import DocScope, ProjectStatus
from app.db.models.job_application import JobApplication
from app.db.models.project import Project

API = "/api/v1"


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_document_upload_list_and_download(http_client, admin_token, seed_data, db):
    project = Project(
        organization_id=seed_data["org"].id,
        name="Proyecto storage",
        status=ProjectStatus.PLANNING,
    )
    doc_type = DocType(name="Contrato storage", scope=DocScope.BOTH)
    db.add_all([project, doc_type])
    db.commit()
    db.refresh(project)
    db.refresh(doc_type)

    created = http_client.post(
        f"{API}/project-docs",
        headers=_headers(admin_token),
        json={
            "project_id": project.id,
            "doc_type_id": doc_type.id,
            "title": "Contrato",
            "github_url": "https://example.com/contrato.pdf",
        },
    )
    assert created.status_code == 201, created.text
    doc_id = created.json()["id"]

    content = b"%PDF-1.4\narchivo real\n%%EOF"
    uploaded = http_client.post(
        f"{API}/project-docs/{doc_id}/file",
        headers=_headers(admin_token),
        files={"file": ("contrato.pdf", content, "application/pdf")},
    )
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["github_url"] == "https://example.com/contrato.pdf"
    assert uploaded.json()["file_name"] == "contrato.pdf"

    listed = http_client.get(f"{API}/project-docs", headers=_headers(admin_token))
    assert listed.status_code == 200
    item = next(row for row in listed.json() if row["id"] == doc_id)
    assert item["file_url"].endswith(f"/{doc_id}/download")

    downloaded = http_client.get(item["file_url"], headers=_headers(admin_token))
    assert downloaded.status_code == 200
    assert downloaded.content == content


def test_cv_upload_is_listed_downloadable_and_preserves_external_urls(
    http_client, admin_token, db
):
    application = JobApplication(
        full_name="Candidata Storage",
        email="[EMAIL_REDACTED]",
        cv_url="https://example.com/cv-original.pdf",
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    content = b"%PDF-1.4\nCV real\n%%EOF"
    uploaded = http_client.post(
        f"{API}/job-applications/{application.id}/attachments/upload",
        headers=_headers(admin_token),
        files={"file": ("cv.pdf", content, "application/pdf")},
    )
    assert uploaded.status_code == 201, uploaded.text
    attachment = uploaded.json()

    listed = http_client.get(
        f"{API}/job-applications/{application.id}/attachments",
        headers=_headers(admin_token),
    )
    assert listed.status_code == 200
    assert any(item["id"] == attachment["id"] for item in listed.json())

    downloaded = http_client.get(attachment["file_url"], headers=_headers(admin_token))
    assert downloaded.status_code == 200
    assert downloaded.content == content


def test_rejects_invalid_document_type(http_client, admin_token, seed_data, db):
    project = Project(
        organization_id=seed_data["org"].id,
        name="Proyecto validación",
        status=ProjectStatus.PLANNING,
    )
    doc_type = DocType(name="Tipo storage inválido", scope=DocScope.BOTH)
    db.add_all([project, doc_type])
    db.commit()
    created = http_client.post(
        f"{API}/project-docs",
        headers=_headers(admin_token),
        json={"project_id": project.id, "doc_type_id": doc_type.id, "title": "Malware"},
    )
    response = http_client.post(
        f"{API}/project-docs/{created.json()['id']}/file",
        headers=_headers(admin_token),
        files={"file": ("payload.exe", b"MZ", "application/octet-stream")},
    )
    assert response.status_code == 415
