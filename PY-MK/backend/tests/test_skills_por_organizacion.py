"""El super_admin solo ve las skills de su organizacion.

`GET /skills/user-skills` saltaba el filtro de organizacion para el super_admin
y le mostraba las skills declaradas en todas las organizaciones.
"""

from __future__ import annotations

from uuid import uuid4

from app.db.models.enums import RoleCode
from app.db.models.organization import Organization
from app.db.models.skill import Skill
from app.db.models.user_skill import UserSkill
from tests.conftest import API
from tests.test_certificados_adjuntos import _usuario


def test_el_super_admin_no_ve_skills_de_otra_organizacion(http_client, db, seed_data):
    org = seed_data["org"]
    otra = Organization(name=f"Otra {uuid4().hex[:6]}", slug=f"otra-{uuid4().hex[:8]}")
    db.add(otra)
    db.commit()
    skill = Skill(name=f"FortiGate {uuid4().hex[:6]}")
    db.add(skill)
    db.commit()
    propio, _ = _usuario(db, org.id, RoleCode.COLLABORATOR)
    ajeno, _ = _usuario(db, otra.id, RoleCode.COLLABORATOR)
    mia = UserSkill(user_id=propio.id, skill_id=skill.id, level="3")
    suya = UserSkill(user_id=ajeno.id, skill_id=skill.id, level="4")
    db.add_all([mia, suya])
    db.commit()
    _, token = _usuario(db, org.id, RoleCode.SUPER_ADMIN)

    r = http_client.get(f"{API}/skills/user-skills", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    ids = {s["id"] for s in r.json()}
    assert mia.id in ids
    assert suya.id not in ids
