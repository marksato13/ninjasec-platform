"""Re-verificacion al editar (21-P-01 / 17-P-04).

El flujo `declarar -> aprobar -> editar` permitia elevar una capacidad ya
verificada sin nueva revision: aprobar "Cisco basico" y editarlo a "CCIE"
conservando el sello. Estos tests fijan que editar lo material revoque la
aprobacion.
"""

from datetime import datetime

from app.db.models.enums import CertificationStatus, SkillStatus
from app.db.models.skill import Skill
from app.db.models.user_certification import UserCertification
from app.db.models.user_skill import UserSkill

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _skill_aprobada(db, user_id, nombre, level="basico"):
    skill = Skill(name=nombre, category="redes")
    db.add(skill)
    db.flush()
    us = UserSkill(
        user_id=user_id,
        skill_id=skill.id,
        level=level,
        status=SkillStatus.APPROVED,
        verified_by=user_id,
        verified_at=datetime.utcnow(),
    )
    db.add(us)
    db.commit()
    return us


# ---------------------------------------------------------------- skills


def test_editar_nivel_aprobado_revoca_la_verificacion(
    db, http_client, admin_token, seed_data
):
    """El caso exacto del hallazgo: basico aprobado -> experto."""
    us = _skill_aprobada(db, seed_data["admin"].id, "Cisco IOS", level="basico")

    res = http_client.put(
        f"{API}/skills/user-skills/{us.id}",
        json={"level": "experto"},
        headers=_auth(admin_token),
    )
    assert res.status_code == 200, res.text

    body = res.json()
    assert body["level"] == "experto"
    assert body["status"] == "pending", (
        "Se elevo una capacidad ya aprobada sin pasar por nueva revision"
    )
    assert body["verified_by"] is None
    assert body["verified_at"] is None


def test_reenviar_el_mismo_nivel_no_revoca(db, http_client, admin_token, seed_data):
    """Guardar el formulario sin cambiar nada no debe penalizar."""
    us = _skill_aprobada(db, seed_data["admin"].id, "FortiGate", level="avanzado")

    res = http_client.put(
        f"{API}/skills/user-skills/{us.id}",
        json={"level": "avanzado"},
        headers=_auth(admin_token),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "approved", (
        "Reenviar el mismo valor no es una edicion y no debe revocar"
    )


def test_editar_skill_pendiente_la_deja_pendiente(db, http_client, admin_token, seed_data):
    skill = Skill(name="MikroTik RouterOS", category="redes")
    db.add(skill)
    db.flush()
    us = UserSkill(
        user_id=seed_data["admin"].id,
        skill_id=skill.id,
        level="basico",
        status=SkillStatus.PENDING,
    )
    db.add(us)
    db.commit()

    res = http_client.put(
        f"{API}/skills/user-skills/{us.id}",
        json={"level": "intermedio"},
        headers=_auth(admin_token),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "pending"


# -------------------------------------------------------- certificaciones


def test_editar_certificacion_aprobada_revoca_la_verificacion(
    db, http_client, admin_token, seed_data
):
    cert = UserCertification(
        user_id=seed_data["admin"].id,
        name="CCNA",
        issuer="Cisco",
        status=CertificationStatus.APPROVED,
        verified_by=seed_data["admin"].id,
        verified_at=datetime.utcnow(),
    )
    db.add(cert)
    db.commit()

    res = http_client.put(
        f"{API}/user-certifications/{cert.id}",
        json={"name": "CCIE"},
        headers=_auth(admin_token),
    )
    assert res.status_code == 200, res.text

    body = res.json()
    assert body["name"] == "CCIE"
    assert body["status"] == "pending", (
        "Se cambio CCNA por CCIE conservando el sello de verificado"
    )
    assert body["verified_by"] is None


def test_editar_certificacion_rechazada_no_la_asciende_a_pendiente(
    db, http_client, admin_token, seed_data
):
    """Una edicion no debe sacar un registro del estado rechazado."""
    cert = UserCertification(
        user_id=seed_data["admin"].id,
        name="Cert Rechazada",
        issuer="Cisco",
        status=CertificationStatus.REJECTED,
    )
    db.add(cert)
    db.commit()

    res = http_client.put(
        f"{API}/user-certifications/{cert.id}",
        json={"name": "Cert Rechazada Editada"},
        headers=_auth(admin_token),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "rejected"


def test_cambiar_expires_at_revoca(db, http_client, admin_token, seed_data):
    """Renovar la vigencia es un dato nuevo que el revisor no vio."""
    cert = UserCertification(
        user_id=seed_data["admin"].id,
        name="CCNP Renovable",
        issuer="Cisco",
        status=CertificationStatus.APPROVED,
        verified_by=seed_data["admin"].id,
        verified_at=datetime.utcnow(),
        expires_at=datetime(2026, 1, 1),
    )
    db.add(cert)
    db.commit()

    res = http_client.put(
        f"{API}/user-certifications/{cert.id}",
        json={"expires_at": "2030-01-01T00:00:00"},
        headers=_auth(admin_token),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "pending"
