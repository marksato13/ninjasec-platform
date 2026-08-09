from app.core.security import create_access_token
from app.db.models.enums import RoleCode, UserStatus
from app.db.models.role import Role
from app.db.models.skill import Skill
from app.db.models.user import User
from app.db.models.user_certification import UserCertification
from app.db.models.user_skill import UserSkill

API = "/api/v1"


def _super_admin(db, seed_data):
    role = db.query(Role).filter(Role.code == RoleCode.SUPER_ADMIN.value).first()
    if role is None:
        role = Role(code=RoleCode.SUPER_ADMIN.value, name="Super Admin")
        db.add(role)
        db.flush()
    user = User(
        organization_id=seed_data["org"].id,
        role_id=role.id,
        full_name="Test Approver",
        email="test-approver@ninjasec.local",
        password_hash="unused",
        role_code=RoleCode.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user, create_access_token(user.email)


def test_rejection_requires_and_exposes_reason(http_client, db, seed_data):
    approver, token = _super_admin(db, seed_data)
    skill = Skill(name="Skill de rechazo", is_active=True)
    db.add(skill)
    db.flush()
    user_skill = UserSkill(user_id=seed_data["collab"].id, skill_id=skill.id)
    certification = UserCertification(
        user_id=seed_data["collab"].id, name="Certificacion de rechazo"
    )
    db.add_all([user_skill, certification])
    db.commit()

    headers = {"Authorization": f"Bearer {token}"}
    invalid = http_client.post(
        f"{API}/skills/user-skills/{user_skill.id}/verify",
        headers=headers,
        json={"status": "rejected", "rejection_reason": "   "},
    )
    assert invalid.status_code == 422
    assert "motivo de rechazo es obligatorio" in invalid.text.lower()

    rejected = http_client.post(
        f"{API}/skills/user-skills/{user_skill.id}/verify",
        headers=headers,
        json={"status": "rejected", "rejection_reason": "Falta evidencia"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["rejection_reason"] == "Falta evidencia"

    collaborator_headers = {
        "Authorization": f"Bearer {create_access_token(seed_data['collab'].email)}"
    }
    own_items = http_client.get(
        f"{API}/skills/user-skills", headers=collaborator_headers
    ).json()
    assert next(item for item in own_items if item["id"] == user_skill.id)[
        "rejection_reason"
    ] == "Falta evidencia"

    count = http_client.get(
        f"{API}/skills/approvals/pending-count", headers=headers
    )
    assert count.status_code == 200
    assert count.json()["pending"] >= 1

    assert approver.id
