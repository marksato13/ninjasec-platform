"""Pruebas de integración de la conversión hired → colaborador (15-P-01)."""

from sqlalchemy import func, select

from app.db.models.collaborator_profile import CollaboratorProfile
from app.db.models.enums import JobApplicationStatus, RoleCode
from app.db.models.job_application import JobApplication
from app.db.models.user import User

from conftest import API


def _application(email: str) -> JobApplication:
    return JobApplication(
        full_name="Ana Postulante",
        email=email,
        phone="+51 999 111 222",
        desired_role="Analista SOC",
        skills_summary='["SIEM", "Python"]',
        cv_url="https://example.com/cv/ana.pdf",
        portfolio_url="https://example.com/ana",
        status=JobApplicationStatus.OFFER,
    )


def test_hired_creates_user_and_profile_from_application(
    http_client, db, admin_token, seed_data
):
    """La contratación crea ambas entidades sin pasos manuales."""
    application = _application("  Ana.Postulante@Example.com ")
    db.add(application)
    db.commit()

    response = http_client.patch(
        f"{API}/job-applications/{application.id}",
        json={"status": "hired"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == JobApplicationStatus.HIRED.value
    user = db.scalar(
        select(User).where(func.lower(User.email) == "ana.postulante@example.com")
    )
    assert user is not None
    assert user.full_name == application.full_name
    assert user.organization_id == seed_data["org"].id
    assert user.role_code == RoleCode.COLLABORATOR
    assert user.job_title == application.desired_role

    profile = db.scalar(
        select(CollaboratorProfile).where(CollaboratorProfile.user_id == user.id)
    )
    assert profile is not None
    assert profile.source_application_id == application.id
    assert profile.phone == application.phone
    assert profile.cv_url == application.cv_url
    assert profile.position_title == application.desired_role
    assert profile.skills_json == application.skills_summary
    assert profile.portfolio_url == application.portfolio_url


def test_hired_with_existing_email_returns_conflict_without_side_effects(
    http_client, db, admin_token, seed_data
):
    """Un email ya registrado deja la postulación intacta y no duplica datos."""
    application = _application(seed_data["collab"].email.upper())
    db.add(application)
    db.commit()
    users_before = db.scalar(select(func.count()).select_from(User))
    profiles_before = db.scalar(select(func.count()).select_from(CollaboratorProfile))

    response = http_client.patch(
        f"{API}/job-applications/{application.id}",
        json={"status": "hired"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 409, response.text
    assert "Ya existe un usuario con el email" in response.json()["detail"]
    db.expire_all()
    assert db.get(JobApplication, application.id).status == JobApplicationStatus.OFFER
    assert db.scalar(select(func.count()).select_from(User)) == users_before
    assert (
        db.scalar(select(func.count()).select_from(CollaboratorProfile))
        == profiles_before
    )
