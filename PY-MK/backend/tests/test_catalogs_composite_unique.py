"""Unicidad de catalogos por organizacion (20-P-09).

`areas.name` y `project_types.name` eran UNIQUE globales pese a llevar
`organization_id`: la primera organizacion que creaba un area "Redes" se
la quedaba y ninguna otra podia tener la suya. El multi-tenant se rompia
al segundo tenant.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models.area import Area
from app.db.models.organization import Organization
from app.db.models.product import Product
from app.db.models.project_type import ProjectType


def _dos_orgs(db):
    a = db.query(Organization).filter(Organization.slug == "tenant-a").first()
    if a is None:
        a = Organization(name="Tenant A", slug="tenant-a")
        db.add(a)
    b = db.query(Organization).filter(Organization.slug == "tenant-b").first()
    if b is None:
        b = Organization(name="Tenant B", slug="tenant-b")
        db.add(b)
    db.commit()
    return a, b


def test_dos_organizaciones_pueden_tener_el_mismo_nombre_de_area(db):
    a, b = _dos_orgs(db)

    db.add(Area(organization_id=a.id, name="Redes", slug="redes"))
    db.commit()

    db.add(Area(organization_id=b.id, name="Redes", slug="redes"))
    db.commit()  # antes reventaba con UNIQUE constraint failed

    nombres = db.query(Area).filter(Area.name == "Redes").all()
    assert len(nombres) == 2
    assert {x.organization_id for x in nombres} == {a.id, b.id}


def test_la_misma_organizacion_no_puede_duplicar_un_area(db):
    a, _ = _dos_orgs(db)

    db.add(Area(organization_id=a.id, name="Ciberseguridad", slug="ciberseguridad"))
    db.commit()

    db.add(Area(organization_id=a.id, name="Ciberseguridad", slug="ciberseguridad-2"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_dos_organizaciones_pueden_tener_el_mismo_tipo_de_proyecto(db):
    a, b = _dos_orgs(db)

    db.add(ProjectType(organization_id=a.id, name="Migración", slug="migracion"))
    db.commit()
    db.add(ProjectType(organization_id=b.id, name="Migración", slug="migracion"))
    db.commit()

    assert db.query(ProjectType).filter(ProjectType.name == "Migración").count() == 2


def test_dos_organizaciones_pueden_tener_el_mismo_producto(db):
    a, b = _dos_orgs(db)

    db.add(Product(organization_id=a.id, name="Firewall Gestionado", slug="firewall-gestionado"))
    db.commit()
    db.add(Product(organization_id=b.id, name="Firewall Gestionado", slug="firewall-gestionado"))
    db.commit()

    assert db.query(Product).filter(Product.slug == "firewall-gestionado").count() == 2


def test_la_misma_organizacion_no_puede_duplicar_el_slug_de_producto(db):
    a, _ = _dos_orgs(db)

    db.add(Product(organization_id=a.id, name="SOC 24x7", slug="soc-24x7"))
    db.commit()

    db.add(Product(organization_id=a.id, name="SOC 24x7 Premium", slug="soc-24x7"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
