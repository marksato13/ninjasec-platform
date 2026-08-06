"""Vigencia de certificaciones (21-P-02 / 17-P-05).

`expires_at` se guardaba y nadie lo evaluaba: una certificacion caducada
seguia figurando como "approved" en el directorio de colaboradores, que es
material de cara al cliente. Estos tests fijan que la vigencia se derive
en cada lectura sin mutar el estado almacenado.
"""

from datetime import datetime, timedelta

from app.db.models.enums import CertificationStatus
from app.db.models.user_certification import UserCertification

API = "/api/v1"


def _crear(db, user_id: int, nombre: str, expires_at, status=CertificationStatus.APPROVED):
    cert = UserCertification(
        user_id=user_id,
        name=nombre,
        issuer="Cisco",
        status=status,
        expires_at=expires_at,
    )
    db.add(cert)
    db.commit()
    return cert


def _buscar(payload, nombre):
    return next(c for c in payload if c["name"] == nombre)


def test_certificacion_vencida_no_se_reporta_como_aprobada(
    db, http_client, admin_token, seed_data
):
    uid = seed_data["admin"].id
    _crear(db, uid, "CCNA Caducada", datetime.utcnow() - timedelta(days=400))

    res = http_client.get(
        f"{API}/user-certifications/", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200, res.text

    cert = _buscar(res.json(), "CCNA Caducada")
    assert cert["is_expired"] is True
    assert cert["effective_status"] == "expired", (
        "Una certificacion caducada se sigue presentando como aprobada al cliente"
    )
    # El hecho historico se conserva: si fue aprobada en su momento.
    assert cert["status"] == "approved"


def test_certificacion_vigente_sigue_aprobada(db, http_client, admin_token, seed_data):
    uid = seed_data["admin"].id
    _crear(db, uid, "CCNP Vigente", datetime.utcnow() + timedelta(days=200))

    res = http_client.get(
        f"{API}/user-certifications/", headers={"Authorization": f"Bearer {admin_token}"}
    )
    cert = _buscar(res.json(), "CCNP Vigente")
    assert cert["is_expired"] is False
    assert cert["effective_status"] == "approved"
    assert 195 <= cert["days_until_expiry"] <= 200


def test_certificacion_sin_fecha_no_caduca(db, http_client, admin_token, seed_data):
    uid = seed_data["admin"].id
    _crear(db, uid, "Certificacion Perpetua", None)

    res = http_client.get(
        f"{API}/user-certifications/", headers={"Authorization": f"Bearer {admin_token}"}
    )
    cert = _buscar(res.json(), "Certificacion Perpetua")
    assert cert["is_expired"] is False
    assert cert["days_until_expiry"] is None
    assert cert["effective_status"] == "approved"


def test_vencida_no_resucita_un_rechazo(db, http_client, admin_token, seed_data):
    """La expiracion no debe pisar un estado que ya era negativo."""
    uid = seed_data["admin"].id
    _crear(
        db, uid, "Cert Rechazada Y Vencida",
        datetime.utcnow() - timedelta(days=10),
        status=CertificationStatus.REJECTED,
    )

    res = http_client.get(
        f"{API}/user-certifications/", headers={"Authorization": f"Bearer {admin_token}"}
    )
    cert = _buscar(res.json(), "Cert Rechazada Y Vencida")
    assert cert["is_expired"] is True
    assert cert["effective_status"] == "rejected", (
        "Un rechazo debe seguir siendo rechazo, no convertirse en 'vencida'"
    )


def test_dias_negativos_cuando_ya_vencio(db, http_client, admin_token, seed_data):
    uid = seed_data["admin"].id
    _crear(db, uid, "Cert Vencida Reciente", datetime.utcnow() - timedelta(days=5))

    res = http_client.get(
        f"{API}/user-certifications/", headers={"Authorization": f"Bearer {admin_token}"}
    )
    cert = _buscar(res.json(), "Cert Vencida Reciente")
    assert cert["days_until_expiry"] is not None
    assert cert["days_until_expiry"] < 0, "Los dias deben ser negativos tras la caducidad"
