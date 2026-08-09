"""Flujos de almacenamiento local con archivos efímeros (19-P-01 y 15-P-02)."""

import pytest

from app.common.storage import storage
from app.core.config import settings
from app.db.models.doc_type import DocType
from app.db.models.enums import DocScope, ProjectStatus
from app.db.models.job_application import JobApplication
from app.db.models.project import Project

API = "/api/v1"


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def temporary_storage(tmp_path, monkeypatch):
    """Aísla los archivos reales de cada prueba fuera del repositorio."""
    monkeypatch.setattr(storage, "root", tmp_path)
    return tmp_path


temporary_storage = pytest.fixture(temporary_storage)


def _create_project_doc(http_client, admin_token, seed_data, db, *, title: str):
    project = Project(
        organization_id=seed_data["org"].id,
        name=f"Proyecto {title}",
        status=ProjectStatus.PLANNING,
    )
    doc_type = DocType(name=f"Contrato {title}", scope=DocScope.BOTH)
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
            "title": title,
            "github_url": "https://example.com/contrato.pdf",
        },
    )
    assert created.status_code == 201, created.text
    return created.json()


def test_document_upload_list_and_download(
    http_client, admin_token, seed_data, db, temporary_storage
):
    document = _create_project_doc(
        http_client, admin_token, seed_data, db, title="storage completo"
    )
    content = b"%PDF-1.4\narchivo real\n%%EOF"
    uploaded = http_client.post(
        f"{API}/project-docs/{document['id']}/file",
        headers=_headers(admin_token),
        files={"file": ("contrato.pdf", content, "application/pdf")},
    )
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["github_url"] == "https://example.com/contrato.pdf"
    assert uploaded.json()["file_name"] == "contrato.pdf"
    assert uploaded.json()["file_size"] == len(content)

    listed = http_client.get(f"{API}/project-docs", headers=_headers(admin_token))
    assert listed.status_code == 200
    item = next(row for row in listed.json() if row["id"] == document["id"])
    assert item["file_url"].endswith(f"/{document['id']}/download")

    downloaded = http_client.get(item["file_url"], headers=_headers(admin_token))
    assert downloaded.status_code == 200
    assert downloaded.content == content
    assert list(temporary_storage.rglob("*.pdf"))


def test_cv_upload_is_persisted_listed_and_downloadable(
    http_client, admin_token, db, temporary_storage
):
    application = JobApplication(
        full_name="Candidata Storage",
        email="candidata.storage@example.com",
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
    assert attachment["file_name"] == "cv.pdf"
    assert attachment["file_size"] == len(content)

    listed = http_client.get(
        f"{API}/job-applications/{application.id}/attachments",
        headers=_headers(admin_token),
    )
    assert listed.status_code == 200
    assert any(item["id"] == attachment["id"] for item in listed.json())

    downloaded = http_client.get(attachment["file_url"], headers=_headers(admin_token))
    assert downloaded.status_code == 200
    assert downloaded.content == content

    persisted = http_client.get(
        f"{API}/job-applications/{application.id}", headers=_headers(admin_token)
    )
    assert persisted.status_code == 200
    assert persisted.json()["cv_url"] == attachment["file_url"]
    assert list(temporary_storage.rglob("*.pdf"))


def test_rejects_invalid_document_type(
    http_client, admin_token, seed_data, db, temporary_storage
):
    document = _create_project_doc(
        http_client, admin_token, seed_data, db, title="validación de tipo"
    )
    response = http_client.post(
        f"{API}/project-docs/{document['id']}/file",
        headers=_headers(admin_token),
        files={"file": ("payload.exe", b"MZ", "application/octet-stream")},
    )
    assert response.status_code == 415
    assert not list(temporary_storage.rglob("*"))


def test_rejects_document_larger_than_storage_limit(
    http_client, admin_token, seed_data, db, temporary_storage
):
    document = _create_project_doc(
        http_client, admin_token, seed_data, db, title="validación de tamaño"
    )
    oversized_content = b"x" * (settings.storage_max_file_size + 1)
    response = http_client.post(
        f"{API}/project-docs/{document['id']}/file",
        headers=_headers(admin_token),
        files={"file": ("demasiado-grande.pdf", oversized_content, "application/pdf")},
    )
    assert response.status_code == 413
    assert not list(temporary_storage.rglob("*"))


def test_external_urls_remain_available_without_storage_migration(
    http_client, admin_token, db
):
    external_cv_url = "https://example.com/cv-historico.pdf"
    application = JobApplication(
        full_name="Candidata URL externa",
        email="candidata.url.externa@example.com",
        cv_url=external_cv_url,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    existing_cv = http_client.get(
        f"{API}/job-applications/{application.id}", headers=_headers(admin_token)
    )
    assert existing_cv.status_code == 200
    assert existing_cv.json()["cv_url"] == external_cv_url

    external_attachment_url = "https://files.example.com/anexo-historico.pdf"
    created = http_client.post(
        f"{API}/job-applications/{application.id}/attachments",
        headers=_headers(admin_token),
        json={"file_url": external_attachment_url, "file_type": "application/pdf"},
    )
    assert created.status_code == 201, created.text

    listed = http_client.get(
        f"{API}/job-applications/{application.id}/attachments",
        headers=_headers(admin_token),
    )
    assert listed.status_code == 200
    assert any(item["file_url"] == external_attachment_url for item in listed.json())
