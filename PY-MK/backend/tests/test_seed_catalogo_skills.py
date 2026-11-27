"""El catálogo de skills: idempotente, conservador y global a propósito."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.db.models.skill import Skill
from app.db.models.user_skill import UserSkill
from app.db.seed_catalogo_skills import CATALOGO, normalizar, sembrar_catalogo_skills

NOMBRES = [n for nombres in CATALOGO.values() for n in nombres]


@pytest.fixture
def limpio(db):
    """Deja la tabla como estaba: borra solo lo que el seed creó durante la prueba."""
    antes = {s.id for s in db.scalars(select(Skill)).all()}
    yield
    db.rollback()
    nuevas = [s for s in db.scalars(select(Skill)).all() if s.id not in antes]
    for s in nuevas:
        db.delete(s)
    db.commit()


def _total(db) -> int:
    return db.scalar(select(func.count()).select_from(Skill))


def test_crea_lo_que_falta(db, limpio):
    previas = {normalizar(s.name) for s in db.scalars(select(Skill)).all()}
    esperadas = sum(1 for n in NOMBRES if normalizar(n) not in previas)
    r = sembrar_catalogo_skills(db)
    assert r["creadas"] == esperadas
    presentes = {normalizar(s.name) for s in db.scalars(select(Skill)).all()}
    assert all(normalizar(n) in presentes for n in NOMBRES)


def test_es_idempotente(db, limpio):
    sembrar_catalogo_skills(db)
    total = _total(db)
    r = sembrar_catalogo_skills(db)
    assert r == {"creadas": 0, "categorizadas": 0}
    assert _total(db) == total, "Sembrar dos veces no puede duplicar"


def test_no_duplica_por_mayusculas_ni_tildes(db, limpio):
    """Si alguien ya declaró «PYTHON» o «Linux » a mano, no aparece «Python» al lado."""
    existente = db.scalar(select(Skill).where(func.lower(Skill.name) == "python"))
    if existente is None:
        existente = Skill(name="PYTHON", category=None, is_active=True)
        db.add(existente)
        db.commit()
    sembrar_catalogo_skills(db)
    pythons = [s for s in db.scalars(select(Skill)).all() if normalizar(s.name) == "python"]
    assert len(pythons) == 1


def test_no_borra_ni_renombra_y_respeta_la_categoria(db, limpio):
    propia = Skill(name="Skill propia de prueba", category="Mía", is_active=True)
    sin_cat = db.scalar(select(Skill).where(func.lower(Skill.name) == "zabbix"))
    if sin_cat is None:
        sin_cat = Skill(name="zabbix", category=None, is_active=True)
        db.add(sin_cat)
    db.add(propia)
    db.commit()
    categoria_previa = sin_cat.category
    sembrar_catalogo_skills(db)
    db.refresh(propia)
    db.refresh(sin_cat)
    assert propia.name == "Skill propia de prueba" and propia.category == "Mía"
    assert sin_cat.name.lower() == "zabbix", "No renombra lo existente"
    assert sin_cat.category == (categoria_previa or "Monitoreo")


def test_el_catalogo_es_global_y_no_toca_lo_de_cada_organizacion(db, limpio):
    """`Skill` no tiene organization_id: el catálogo es único. Lo que es de cada
    organización (quién declara qué) vive en UserSkill, y el seed no lo toca."""
    assert "organization_id" not in Skill.__table__.columns
    antes = db.scalar(select(func.count()).select_from(UserSkill))
    sembrar_catalogo_skills(db)
    assert db.scalar(select(func.count()).select_from(UserSkill)) == antes


def test_nombres_unicos_y_caben_en_la_columna():
    claves = [normalizar(n) for n in NOMBRES]
    assert len(claves) == len(set(claves))
    assert all(len(n) <= 120 for n in NOMBRES)
    assert all(len(c) <= 80 for c in CATALOGO)


def test_cada_skill_tiene_logo_en_el_frontend():
    """Los nombres deben resolverse en `marcas.ts` (por nombre o alias), o la
    skill sale sin logo. Se salta si el frontend no está en el checkout."""
    marcas = Path(__file__).resolve().parents[2] / "frontend" / "src" / "lib" / "marcas.ts"
    if not marcas.exists():
        pytest.skip("frontend no disponible")
    texto = marcas.read_text(encoding="utf-8")
    conocidos: set[str] = set()
    for linea in texto.splitlines():
        if "slug:" not in linea:
            continue
        for campo in re.findall(r'nombre: "([^"]+)"', linea):
            conocidos.add(normalizar(campo))
        alias = re.search(r"aliases: \[([^\]]*)\]", linea)
        if alias:
            conocidos.update(normalizar(a) for a in re.findall(r'"([^"]+)"', alias.group(1)))
    faltan = [n for n in NOMBRES if normalizar(n) not in conocidos]
    assert not faltan, f"Sin logo: {faltan}"
