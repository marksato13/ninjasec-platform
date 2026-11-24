"""El contenido de los planes de estudio es coherente y se puede resembrar.

Un temario con horas que no suman, módulos sin laboratorio o pesos
inventados no sirve para planificar meses de estudio: sirve para engañarse.
Estas pruebas fijan lo mínimo para que sea utilizable.
"""

from __future__ import annotations

import pytest

from app.db.seed_planes_estudio import CCNA, NSE4, PLANES


TODOS = {plan["slug"]: plan for plan in PLANES}


# --------------------------------------------------------------------------
# Coherencia del contenido
# --------------------------------------------------------------------------


@pytest.mark.parametrize("slug", sorted(TODOS))
def test_las_horas_del_plan_son_la_suma_de_sus_modulos(slug):
    """Antes eran un número escrito a mano al lado, y ya no cuadraban:
    NSE 4 declaraba 120 y sus módulos sumaban 134."""
    plan = TODOS[slug]
    suma = sum(m.get("estimated_hours") or 0 for m in plan["modules"])

    assert plan["estimated_hours"] == suma, (
        f"{slug}: el plan dice {plan['estimated_hours']}h y sus módulos suman {suma}h"
    )


@pytest.mark.parametrize("slug", sorted(TODOS))
def test_todo_modulo_tiene_objetivo_demostrable(slug):
    """Un objetivo que no se puede demostrar no sirve para medir progreso."""
    sin_objetivo = [
        m["title"] for m in TODOS[slug]["modules"] if not (m.get("objective") or "").strip()
    ]

    assert not sin_objetivo, f"{slug}: módulos sin objetivo: {sin_objetivo}"


@pytest.mark.parametrize("slug", sorted(TODOS))
def test_todo_modulo_tiene_laboratorio(slug):
    """Ni NSE 4 ni CCNA se aprueban leyendo."""
    sin_lab = [m["title"] for m in TODOS[slug]["modules"] if not (m.get("lab") or "").strip()]

    assert not sin_lab, f"{slug}: módulos sin laboratorio: {sin_lab}"


@pytest.mark.parametrize("slug", sorted(TODOS))
def test_todo_modulo_tiene_horas(slug):
    sin_horas = [m["title"] for m in TODOS[slug]["modules"] if not m.get("estimated_hours")]

    assert not sin_horas, f"{slug}: módulos sin horas estimadas: {sin_horas}"


@pytest.mark.parametrize("slug", sorted(TODOS))
def test_no_hay_titulos_repetidos(slug):
    titulos = [m["title"] for m in TODOS[slug]["modules"]]

    assert len(titulos) == len(set(titulos)), f"{slug}: hay títulos repetidos"


def test_los_pesos_de_ccna_suman_cien():
    """Los dominios del 200-301 los publica Cisco y suman 100%."""
    suma = sum(m.get("weight_percent") or 0 for m in CCNA["modules"])

    assert suma == 100, f"Los pesos de CCNA suman {suma}%, no 100%"


def test_nse4_no_declara_pesos_inventados():
    """Fortinet no publica porcentajes por tema como hace Cisco.

    En la primera versión se pusieron igualmente, sumando un 75% que no
    significaba nada. Un dato inventado es peor que un dato ausente: el
    ausente se nota.
    """
    con_peso = [m["title"] for m in NSE4["modules"] if m.get("weight_percent")]

    assert not con_peso, (
        "NSE 4 no debe declarar weight_percent mientras Fortinet no publique "
        f"esos porcentajes. Lo declaran: {con_peso}"
    )


@pytest.mark.parametrize("slug", sorted(TODOS))
def test_los_temas_van_uno_por_linea(slug):
    """El formato importa: la interfaz los pinta como lista."""
    plan = TODOS[slug]
    de_una_linea = [
        m["title"]
        for m in plan["modules"]
        if (m.get("topics") or "").strip() and "\n" not in m["topics"].strip()
    ]

    assert not de_una_linea, (
        f"{slug}: estos módulos tienen los temas en una sola línea: {de_una_linea}"
    )


@pytest.mark.parametrize("slug", sorted(TODOS))
def test_el_plan_declara_a_que_certificacion_lleva(slug):
    """Sirve para cerrar el círculo contra `user_certifications.name`."""
    plan = TODOS[slug]

    assert plan.get("target_certification"), f"{slug}: sin certificación objetivo"
    assert plan.get("exam_code"), f"{slug}: sin código de examen"
    assert plan.get("vendor"), f"{slug}: sin fabricante"


# --------------------------------------------------------------------------
# La siembra
# --------------------------------------------------------------------------


def test_sembrar_es_idempotente(db, seed_data):
    """Volver a ejecutarlo no duplica ni deja módulos sueltos de la versión
    anterior del temario."""
    from sqlalchemy import func, select

    from app.db.models.study_plan import StudyModule, StudyPlan
    from app.db.seed_planes_estudio import sembrar_planes_de_estudio

    sembrar_planes_de_estudio(db, seed_data["org"].id)
    planes_1 = db.scalar(select(func.count()).select_from(StudyPlan))
    modulos_1 = db.scalar(select(func.count()).select_from(StudyModule))

    sembrar_planes_de_estudio(db, seed_data["org"].id)
    planes_2 = db.scalar(select(func.count()).select_from(StudyPlan))
    modulos_2 = db.scalar(select(func.count()).select_from(StudyModule))

    assert (planes_1, modulos_1) == (planes_2, modulos_2), (
        "Resembrar duplicó filas: "
        f"planes {planes_1}->{planes_2}, módulos {modulos_1}->{modulos_2}"
    )
    assert planes_1 == len(PLANES)


def test_los_modulos_quedan_en_orden(db, seed_data):
    from sqlalchemy import select

    from app.db.models.study_plan import StudyPlan
    from app.db.seed_planes_estudio import sembrar_planes_de_estudio

    sembrar_planes_de_estudio(db, seed_data["org"].id)
    plan = db.scalar(
        select(StudyPlan).where(StudyPlan.slug == "cisco-ccna-200-301")
    )

    posiciones = [m.position for m in plan.modules]

    assert posiciones == list(range(1, len(posiciones) + 1)), (
        f"Las posiciones no son correlativas desde 1: {posiciones}"
    )


def test_el_plan_pertenece_a_una_organizacion(db, seed_data):
    """No se cuelga de `recruitment`, que no tiene tenant y haría los datos
    globales."""
    from sqlalchemy import select

    from app.db.models.study_plan import StudyPlan
    from app.db.seed_planes_estudio import sembrar_planes_de_estudio

    sembrar_planes_de_estudio(db, seed_data["org"].id)
    planes = db.scalars(select(StudyPlan)).all()

    assert planes
    assert all(p.organization_id == seed_data["org"].id for p in planes)
