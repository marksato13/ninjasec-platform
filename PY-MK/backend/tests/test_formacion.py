"""Formación: inscripción, avance ponderado, validación y aislamiento."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.enums import RoleCode, UserStatus
from app.db.models.organization import Organization
from app.db.models.role import Role
from app.db.models.study_plan import StudyEnrollment, StudyModule, StudyPlan, StudyProgress
from app.db.models.user import User

API = "/api/v1/study"
LOGIN = "/api/v1/auth/login"
CLAVE = "formacion-password-123"


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


def _rol(db, code):
    r = db.scalar(select(Role).where(Role.code == code.value))
    if r is None:
        r = Role(code=code.value, name=code.value)
        db.add(r)
        db.flush()
    return r


def _org(db, slug):
    o = db.scalar(select(Organization).where(Organization.slug == slug))
    if o is None:
        o = Organization(name=slug, slug=slug)
        db.add(o)
        db.commit()
    return o


def _usuario(db, org, code, email):
    if not db.scalar(select(User).where(User.email == email)):
        db.add(User(organization_id=org.id, role_id=_rol(db, code).id, full_name=email.split("@")[0],
                    email=email, password_hash=hash_password(CLAVE), role_code=code,
                    status=UserStatus.ACTIVE, is_active=True))
        db.commit()


def _token(http_client, email):
    r = http_client.post(LOGIN, json={"email": email, "password": CLAVE})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _plan(db, org, slug="plan-prueba"):
    plan = db.scalar(select(StudyPlan).where(StudyPlan.organization_id == org.id, StudyPlan.slug == slug))
    if plan is None:
        plan = StudyPlan(organization_id=org.id, name="Plan de prueba", slug=slug, area="redes",
                         exam_code="X-1", estimated_hours=22, is_active=True)
        db.add(plan)
        db.flush()
        db.add_all([
            StudyModule(plan_id=plan.id, position=1, title="Corto", estimated_hours=2),
            StudyModule(plan_id=plan.id, position=2, title="Largo", estimated_hours=20),
        ])
        db.commit()
    return plan


@pytest.fixture(autouse=True)
def limpio(db):
    def borrar():
        db.query(StudyProgress).delete()
        db.query(StudyEnrollment).delete()
        # Los planes que crean ESTAS pruebas, y solo esos: la base dura toda la sesion y
        # test_planes_de_estudio cuenta los planes que hay. Dejarlos rompia esas pruebas.
        propias = db.scalars(select(StudyPlan.id).join(
            Organization, Organization.id == StudyPlan.organization_id
        ).where(Organization.slug.like("formacion-%"))).all()
        if propias:
            db.query(StudyModule).filter(StudyModule.plan_id.in_(propias)).delete(synchronize_session=False)
            db.query(StudyPlan).filter(StudyPlan.id.in_(propias)).delete(synchronize_session=False)
        db.commit()
    borrar()
    yield
    borrar()


@pytest.fixture
def org(db, seed_data):
    return _org(db, "formacion-a")


@pytest.fixture
def colab(db, http_client, org):
    _usuario(db, org, RoleCode.COLLABORATOR, "form-colab@ninjasec.local")
    return _token(http_client, "form-colab@ninjasec.local")


@pytest.fixture
def colab2(db, http_client, org):
    _usuario(db, org, RoleCode.COLLABORATOR, "form-colab2@ninjasec.local")
    return _token(http_client, "form-colab2@ninjasec.local")


@pytest.fixture
def admin(db, http_client, org):
    _usuario(db, org, RoleCode.ADMIN, "form-admin@ninjasec.local")
    return _token(http_client, "form-admin@ninjasec.local")


@pytest.fixture
def plan(db, org):
    return _plan(db, org)


def _inscribir(http_client, token, plan_id):
    r = http_client.post(f"{API}/plans/{plan_id}/enroll", headers=_auth(token), json={})
    assert r.status_code == 201, r.text
    return r.json()


def _marcar(http_client, token, insc_id, mod_id, estado, **extra):
    return http_client.patch(f"{API}/me/{insc_id}/modules/{mod_id}", headers=_auth(token),
                             json={"status": estado, **extra})


def _modulos(db, plan):
    return db.scalars(select(StudyModule).where(StudyModule.plan_id == plan.id)
                      .order_by(StudyModule.position)).all()


# --- planes ---------------------------------------------------------------


def test_un_cliente_no_ve_los_planes(db, http_client, org):
    _usuario(db, org, RoleCode.CLIENT, "form-cliente@ninjasec.local")
    t = _token(http_client, "form-cliente@ninjasec.local")
    assert http_client.get(f"{API}/plans", headers=_auth(t)).status_code == 403


def test_el_colaborador_lista_y_ve_un_plan(http_client, colab, plan):
    lista = http_client.get(f"{API}/plans", headers=_auth(colab)).json()
    assert plan.id in [p["id"] for p in lista]
    detalle = http_client.get(f"{API}/plans/{plan.id}", headers=_auth(colab)).json()
    assert [m["title"] for m in detalle["modules"]] == ["Corto", "Largo"]


def test_el_plan_de_otra_organizacion_es_404(db, http_client, colab):
    ajena = _plan(db, _org(db, "formacion-b"), slug="plan-ajeno")
    assert http_client.get(f"{API}/plans/{ajena.id}", headers=_auth(colab)).status_code == 404
    assert http_client.post(f"{API}/plans/{ajena.id}/enroll", headers=_auth(colab), json={}).status_code == 404


# --- inscripcion y avance -------------------------------------------------


def test_inscribirse_dos_veces_es_409(http_client, colab, plan):
    _inscribir(http_client, colab, plan.id)
    r = http_client.post(f"{API}/plans/{plan.id}/enroll", headers=_auth(colab), json={})
    assert r.status_code == 409


def test_el_porcentaje_se_pondera_por_horas(db, http_client, colab, plan):
    """Completar el modulo de 2 h de 22 h NO es el 50 %: es el 9 %."""
    insc = _inscribir(http_client, colab, plan.id)
    corto, largo = _modulos(db, plan)
    assert insc["percent"] == 0

    r = _marcar(http_client, colab, insc["id"], corto.id, "completed")
    assert r.json()["percent"] == 9
    assert r.json()["modules_done"] == 1

    r = _marcar(http_client, colab, insc["id"], largo.id, "completed")
    assert r.json()["percent"] == 100


def test_en_progreso_no_cuenta_como_hecho(db, http_client, colab, plan):
    insc = _inscribir(http_client, colab, plan.id)
    _, largo = _modulos(db, plan)
    assert _marcar(http_client, colab, insc["id"], largo.id, "in_progress").json()["percent"] == 0


def test_se_guardan_horas_evidencia_y_notas(db, http_client, colab, plan):
    insc = _inscribir(http_client, colab, plan.id)
    corto, _ = _modulos(db, plan)
    _marcar(http_client, colab, insc["id"], corto.id, "completed", hours_spent=3,
            evidence_url="https://ejemplo.org/captura", notes="Laboratorio de VLAN")
    det = http_client.get(f"{API}/me/{insc['id']}", headers=_auth(colab)).json()
    fila = next(m for m in det["modules"] if m["id"] == corto.id)
    assert (fila["status"], fila["hours_spent"], fila["notes"]) == ("completed", 3, "Laboratorio de VLAN")


def test_un_estado_inventado_se_rechaza(db, http_client, colab, plan):
    insc = _inscribir(http_client, colab, plan.id)
    corto, _ = _modulos(db, plan)
    # 'validated' solo lo pone un admin: quien estudia no se lo puede dar solo.
    assert _marcar(http_client, colab, insc["id"], corto.id, "validated").status_code == 422


def test_un_modulo_de_otro_plan_es_404(db, http_client, colab, plan):
    otro = _plan(db, _org(db, "formacion-a"), slug="otro-plan")
    insc = _inscribir(http_client, colab, plan.id)
    ajeno = _modulos(db, otro)[0]
    assert _marcar(http_client, colab, insc["id"], ajeno.id, "completed").status_code == 404


# --- aislamiento entre personas -------------------------------------------


def test_no_se_ve_ni_se_toca_la_inscripcion_de_otra_persona(db, http_client, colab, colab2, plan):
    insc = _inscribir(http_client, colab, plan.id)
    corto, _ = _modulos(db, plan)
    # 404, no 403: no se confirma que exista.
    assert http_client.get(f"{API}/me/{insc['id']}", headers=_auth(colab2)).status_code == 404
    assert _marcar(http_client, colab2, insc["id"], corto.id, "completed").status_code == 404
    assert http_client.get(f"{API}/me", headers=_auth(colab2)).json() == []


# --- validacion -----------------------------------------------------------


def test_el_admin_valida_un_modulo_completado(db, http_client, colab, admin, plan):
    insc = _inscribir(http_client, colab, plan.id)
    corto, _ = _modulos(db, plan)
    _marcar(http_client, colab, insc["id"], corto.id, "completed")
    pid = db.scalar(select(StudyProgress.id).where(StudyProgress.module_id == corto.id))

    equipo = http_client.get(f"{API}/team", headers=_auth(admin)).json()
    assert equipo[0]["pending_validation"] == 1

    assert http_client.post(f"{API}/progress/{pid}/validate", headers=_auth(admin)).status_code == 200
    det = http_client.get(f"{API}/me/{insc['id']}", headers=_auth(colab)).json()
    assert next(m for m in det["modules"] if m["id"] == corto.id)["validated"] is True
    assert http_client.get(f"{API}/team", headers=_auth(admin)).json()[0]["pending_validation"] == 0


def test_lo_validado_no_se_puede_retroceder(db, http_client, colab, admin, plan):
    insc = _inscribir(http_client, colab, plan.id)
    corto, _ = _modulos(db, plan)
    _marcar(http_client, colab, insc["id"], corto.id, "completed")
    pid = db.scalar(select(StudyProgress.id).where(StudyProgress.module_id == corto.id))
    http_client.post(f"{API}/progress/{pid}/validate", headers=_auth(admin))
    assert _marcar(http_client, colab, insc["id"], corto.id, "pending").status_code == 409


def test_no_se_valida_lo_que_no_esta_completado(db, http_client, colab, admin, plan):
    insc = _inscribir(http_client, colab, plan.id)
    corto, _ = _modulos(db, plan)
    _marcar(http_client, colab, insc["id"], corto.id, "in_progress")
    pid = db.scalar(select(StudyProgress.id).where(StudyProgress.module_id == corto.id))
    assert http_client.post(f"{API}/progress/{pid}/validate", headers=_auth(admin)).status_code == 409


def test_nadie_valida_su_propio_avance(db, http_client, admin, plan):
    insc = _inscribir(http_client, admin, plan.id)
    corto, _ = _modulos(db, plan)
    _marcar(http_client, admin, insc["id"], corto.id, "completed")
    pid = db.scalar(select(StudyProgress.id).where(StudyProgress.module_id == corto.id))
    assert http_client.post(f"{API}/progress/{pid}/validate", headers=_auth(admin)).status_code == 403


def test_el_colaborador_no_valida_ni_ve_al_equipo(db, http_client, colab, colab2, plan):
    insc = _inscribir(http_client, colab, plan.id)
    corto, _ = _modulos(db, plan)
    _marcar(http_client, colab, insc["id"], corto.id, "completed")
    pid = db.scalar(select(StudyProgress.id).where(StudyProgress.module_id == corto.id))
    assert http_client.post(f"{API}/progress/{pid}/validate", headers=_auth(colab2)).status_code == 403
    assert http_client.get(f"{API}/team", headers=_auth(colab2)).status_code == 403


def test_otra_organizacion_no_valida_mi_avance(db, http_client, colab, plan):
    insc = _inscribir(http_client, colab, plan.id)
    corto, _ = _modulos(db, plan)
    _marcar(http_client, colab, insc["id"], corto.id, "completed")
    pid = db.scalar(select(StudyProgress.id).where(StudyProgress.module_id == corto.id))
    otra = _org(db, "formacion-b")
    _usuario(db, otra, RoleCode.ADMIN, "form-admin-b@ninjasec.local")
    t = _token(http_client, "form-admin-b@ninjasec.local")
    assert http_client.post(f"{API}/progress/{pid}/validate", headers=_auth(t)).status_code == 404
    assert http_client.get(f"{API}/team", headers=_auth(t)).json() == []


def test_el_admin_ve_el_detalle_de_otra_persona_para_validar(db, http_client, colab, admin, plan):
    insc = _inscribir(http_client, colab, plan.id)
    corto, _ = _modulos(db, plan)
    _marcar(http_client, colab, insc["id"], corto.id, "completed")
    det = http_client.get(f"{API}/team/{insc['id']}", headers=_auth(admin)).json()
    fila = next(m for m in det["modules"] if m["id"] == corto.id)
    assert fila["status"] == "completed" and fila["progress_id"] is not None


def test_el_detalle_del_equipo_es_solo_de_admin_y_de_su_organizacion(db, http_client, colab, colab2, plan):
    insc = _inscribir(http_client, colab, plan.id)
    assert http_client.get(f"{API}/team/{insc['id']}", headers=_auth(colab2)).status_code == 403
    otra = _org(db, "formacion-b")
    _usuario(db, otra, RoleCode.ADMIN, "form-admin-b@ninjasec.local")
    tb = _token(http_client, "form-admin-b@ninjasec.local")
    assert http_client.get(f"{API}/team/{insc['id']}", headers=_auth(tb)).status_code == 404
