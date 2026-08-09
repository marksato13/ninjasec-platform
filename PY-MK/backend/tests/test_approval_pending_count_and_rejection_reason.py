"""Cobertura de 17-P-01 y 17-P-02: bandeja de aprobaciones trazable."""

from uuid import uuid4

from app.core.security import create_access_token
from app.db.models.enums import (
    CertificationStatus,
    RoleCode,
    SkillStatus,
    UserStatus,
)
from app.db.models.role import Role
from app.db.models.skill import Skill
from app.db.models.user import User
from app.db.models.user_certification import UserCertification
from app.db.models.user_skill import UserSkill

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _super_admin(db, seed_data):
    role = db.query(Role).filter(Role.code == RoleCode.SUPER_ADMIN.value).first()
    if role is None:
        role = Role(code=RoleCode.SUPER_ADMIN.value, name="Super Admin")
        db.add(role)
        db.flush()

    identifier = uuid4().hex[:12]
    user = User(
        organization_id=seed_data["org"].id,
        role_id=role.id,
        full_name=f"Aprobador de pruebas {identifier}",
        email=f"approver-17-p-{identifier}@ninjasec.local",
        password_hash="unused",
        role_code=RoleCode.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user, create_access_token(user.email)


def _pending_items(db, user_id, suffix):
    skill = Skill(name=f"Skill pendiente {suffix}", category="redes", is_active=True)
    db.add(skill)
    db.flush()
    user_skill = UserSkill(
        user_id=user_id, skill_id=skill.id, status=SkillStatus.PENDING
    )
    certification = UserCertification(
        user_id=user_id,
        name=f"Certificacion pendiente {suffix}",
        status=CertificationStatus.PENDING,
    )
    db.add_all([user_skill, certification])
    db.commit()
    return user_skill, certification


def _collaborator(db, seed_data):
    identifier = uuid4().hex[:12]
    role = db.query(Role).filter(Role.code == RoleCode.COLLABORATOR.value).one()
    user = User(
        organization_id=seed_data["org"].id,
        role_id=role.id,
        full_name=f"Otro solicitante {identifier}",
        email=f"otro-solicitante-{identifier}@ninjasec.local",
        password_hash="unused",
        role_code=RoleCode.COLLABORATOR,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def _pending_count(http_client, token):
    response = http_client.get(
        f"{API}/skills/approvals/pending-count", headers=_auth(token)
    )
    assert response.status_code == 200, response.text
    return response.json()["pending"]


def test_contador_suma_solo_pendientes_y_exige_super_admin(
    db, http_client, seed_data, admin_token, collaborator_token
):
    """El badge representa exactamente solicitudes pending de skills y certs."""
    _, super_admin_token = _super_admin(db, seed_data)
    before = _pending_count(http_client, super_admin_token)
    user_skill, certification = _pending_items(db, seed_data["collab"].id, "conteo")

    # Estos registros no pueden inflar el indicador de solicitudes pendientes.
    approved_skill = Skill(name="Skill aprobada conteo", is_active=True)
    db.add(approved_skill)
    db.flush()
    db.add(UserSkill(
        user_id=seed_data["collab"].id,
        skill_id=approved_skill.id,
        status=SkillStatus.APPROVED,
    ))
    db.commit()

    assert _pending_count(http_client, super_admin_token) == before + 2
    assert user_skill.status == SkillStatus.PENDING
    assert certification.status == CertificationStatus.PENDING

    for token in (admin_token, collaborator_token):
        denied = http_client.get(
            f"{API}/skills/approvals/pending-count", headers=_auth(token)
        )
        assert denied.status_code == 403


def test_contador_disminuye_despues_de_aprobar_y_rechazar(
    db, http_client, seed_data
):
    """Cada resolución saca una solicitud de pending inmediatamente."""
    _, token = _super_admin(db, seed_data)
    before = _pending_count(http_client, token)
    user_skill, certification = _pending_items(db, seed_data["collab"].id, "resolver")
    assert _pending_count(http_client, token) == before + 2

    approved = http_client.post(
        f"{API}/skills/user-skills/{user_skill.id}/verify",
        headers=_auth(token),
        json={"status": "approved"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"
    assert _pending_count(http_client, token) == before + 1

    rejected = http_client.post(
        f"{API}/user-certifications/{certification.id}/verify",
        headers=_auth(token),
        json={"status": "rejected", "rejection_reason": "Falta evidencia vigente"},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "rejected"
    assert _pending_count(http_client, token) == before


def test_rechazo_vacio_no_persiste_y_solo_super_admin_puede_resolver(
    db, http_client, seed_data, admin_token, collaborator_token
):
    _, super_admin_token = _super_admin(db, seed_data)
    user_skill, certification = _pending_items(db, seed_data["collab"].id, "motivo")

    for url in (
        f"{API}/skills/user-skills/{user_skill.id}/verify",
        f"{API}/user-certifications/{certification.id}/verify",
    ):
        empty_reason = http_client.post(
            url,
            headers=_auth(super_admin_token),
            json={"status": "rejected", "rejection_reason": "   "},
        )
        assert empty_reason.status_code == 422
        assert "motivo de rechazo es obligatorio" in empty_reason.text.lower()

        for token in (admin_token, collaborator_token):
            denied = http_client.post(
                url,
                headers=_auth(token),
                json={"status": "approved"},
            )
            assert denied.status_code == 403

    db.refresh(user_skill)
    db.refresh(certification)
    assert user_skill.status == SkillStatus.PENDING
    assert certification.status == CertificationStatus.PENDING


def test_motivo_rechazo_persistido_es_visible_para_el_solicitante_original(
    db, http_client, seed_data
):
    """El colaborador solo recibe sus detalles, incluido el motivo rechazado."""
    _, super_admin_token = _super_admin(db, seed_data)
    user_skill, certification = _pending_items(db, seed_data["collab"].id, "visibilidad")

    skill_reason = "Adjunta evidencia de experiencia practica"
    cert_reason = "El identificador de la credencial no es verificable"
    assert http_client.post(
        f"{API}/skills/user-skills/{user_skill.id}/verify",
        headers=_auth(super_admin_token),
        json={"status": "rejected", "rejection_reason": skill_reason},
    ).status_code == 200
    assert http_client.post(
        f"{API}/user-certifications/{certification.id}/verify",
        headers=_auth(super_admin_token),
        json={"status": "rejected", "rejection_reason": cert_reason},
    ).status_code == 200

    requester_token = create_access_token(seed_data["collab"].email)
    skills = http_client.get(
        f"{API}/skills/user-skills", headers=_auth(requester_token)
    )
    certifications = http_client.get(
        f"{API}/user-certifications/", headers=_auth(requester_token)
    )
    assert skills.status_code == certifications.status_code == 200

    own_skill = next(item for item in skills.json() if item["id"] == user_skill.id)
    own_certification = next(
        item for item in certifications.json() if item["id"] == certification.id
    )
    assert own_skill["rejection_reason"] == skill_reason
    assert own_certification["rejection_reason"] == cert_reason

    other_requester = _collaborator(db, seed_data)
    other_token = create_access_token(other_requester.email)
    other_skills = http_client.get(
        f"{API}/skills/user-skills", headers=_auth(other_token)
    )
    other_certifications = http_client.get(
        f"{API}/user-certifications/", headers=_auth(other_token)
    )
    assert other_skills.status_code == other_certifications.status_code == 200
    assert all(item["id"] != user_skill.id for item in other_skills.json())
    assert all(item["id"] != certification.id for item in other_certifications.json())
