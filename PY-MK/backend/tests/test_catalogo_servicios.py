"""El catálogo de servicios: contenido sembrable, idempotente y sin promesas falsas."""

from __future__ import annotations

import re

import pytest
from sqlalchemy import func, select

from app.db.models.organization import Organization
from app.db.models.service import Service
from app.db.seed_catalogo_servicios import PRECIO, SERVICIOS, sembrar_catalogo_servicios


@pytest.fixture
def org(db):
    org = db.scalar(select(Organization).where(Organization.slug == "catalogo-test"))
    if org is None:
        org = Organization(name="Catalogo Test", slug="catalogo-test")
        db.add(org)
        db.commit()
    yield org
    db.query(Service).filter(Service.organization_id == org.id).delete()
    db.commit()


def test_siembra_todos_los_servicios(db, org):
    assert sembrar_catalogo_servicios(db, org.id) == len(SERVICIOS)
    n = db.scalar(select(func.count()).select_from(Service).where(Service.organization_id == org.id))
    assert n == len(SERVICIOS)


def test_es_idempotente(db, org):
    sembrar_catalogo_servicios(db, org.id)
    sembrar_catalogo_servicios(db, org.id)
    n = db.scalar(select(func.count()).select_from(Service).where(Service.organization_id == org.id))
    assert n == len(SERVICIOS), "Sembrar dos veces no puede duplicar"


def test_corregir_un_texto_actualiza_en_vez_de_duplicar(db, org):
    sembrar_catalogo_servicios(db, org.id)
    s = db.scalar(select(Service).where(Service.organization_id == org.id,
                                        Service.slug == "sistemas-a-medida"))
    s.summary = "texto viejo"
    db.commit()
    sembrar_catalogo_servicios(db, org.id)
    db.refresh(s)
    assert s.summary != "texto viejo"


def test_cada_servicio_queda_en_su_organizacion(db, org):
    otra = Organization(name="Otra Cat", slug="catalogo-test-otra")
    db.add(otra)
    db.commit()
    try:
        sembrar_catalogo_servicios(db, org.id)
        assert db.scalar(select(func.count()).select_from(Service).where(
            Service.organization_id == otra.id)) == 0
    finally:
        db.delete(otra)
        db.commit()


def test_los_slugs_no_se_repiten():
    slugs = [s["slug"] for s in SERVICIOS]
    assert len(slugs) == len(set(slugs))


def test_los_textos_caben_en_las_columnas():
    for s in SERVICIOS:
        assert len(s["title"]) <= 120, s["slug"]
        assert len(s["slug"]) <= 120, s["slug"]
        assert len(s["summary"]) <= 255, s["slug"]
        assert len(s["description"]) <= 1000, s["slug"]


def test_cubre_infraestructura_nube_seguridad_y_desarrollo():
    assert {s["category"] for s in SERVICIOS} == {"infraestructura", "nube", "seguridad", "desarrollo"}


def test_no_promete_lo_que_el_catalogo_comercial_dice_que_no_se_vende():
    """Conectores a equipos, informe SOC y hardening automatizado: los
    conectores son simulados, y un cliente tecnico lo descubre en la primera
    demo. Si alguien los anade aqui, esta prueba lo caza."""
    prohibidas = re.compile(r"conector|informe soc|hardening automatiz|nos conectamos|reporting por api", re.I)
    for s in SERVICIOS:
        texto = f"{s['title']} {s['summary']} {s['description']}"
        assert not prohibidas.search(texto), f"{s['slug']}: {prohibidas.search(texto).group(0)}"


def test_no_publica_precios():
    """Los precios son una propuesta sin validar y viven en el repositorio privado."""
    assert PRECIO == "A cotizar"
    for s in SERVICIOS:
        assert not re.search(r"S/\s?\d|USD\s?\d|\$\s?\d", f"{s['summary']} {s['description']}"), s["slug"]
