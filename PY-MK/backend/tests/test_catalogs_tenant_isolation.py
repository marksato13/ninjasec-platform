"""Aislamiento entre organizaciones en los catalogos (20-P-08 / 20-P-10).

`GET /products` devolvia los productos de TODAS las organizaciones pese a que
`Product.organization_id` es NOT NULL. Cualquier usuario autenticado veia el
catalogo ajeno. Estos tests fijan el comportamiento correcto.
"""

from app.db.models.area import Area
from app.db.models.organization import Organization
from app.db.models.product import Product
from app.db.models.project_type import ProjectType

API = "/api/v1"


def _other_org(db):
    """Una segunda organizacion, ajena a la del usuario de los tests."""
    org = db.query(Organization).filter(Organization.slug == "org-ajena").first()
    if org is None:
        org = Organization(name="Organizacion Ajena", slug="org-ajena")
        db.add(org)
        db.commit()
    return org


def test_products_no_filtra_entre_organizaciones(db, http_client, admin_token, seed_data):
    propia = seed_data["org"]
    ajena = _other_org(db)

    db.add_all([
        Product(organization_id=propia.id, name="Producto Propio", slug="producto-propio"),
        Product(organization_id=ajena.id, name="Producto Ajeno", slug="producto-ajeno"),
    ])
    db.commit()

    res = http_client.get(f"{API}/products", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200, res.text

    nombres = {p["name"] for p in res.json()}
    assert "Producto Propio" in nombres
    assert "Producto Ajeno" not in nombres, (
        "Fuga entre tenants: el catalogo expone productos de otra organizacion"
    )


def test_products_omite_inactivos(db, http_client, admin_token, seed_data):
    propia = seed_data["org"]
    db.add(Product(
        organization_id=propia.id,
        name="Producto Retirado",
        slug="producto-retirado",
        is_active=False,
    ))
    db.commit()

    res = http_client.get(f"{API}/products", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert "Producto Retirado" not in {p["name"] for p in res.json()}


def test_areas_muestra_propias_y_globales_pero_no_ajenas(
    db, http_client, admin_token, seed_data
):
    """Area.organization_id es nullable: NULL = catalogo compartido."""
    propia = seed_data["org"]
    ajena = _other_org(db)

    db.add_all([
        Area(organization_id=propia.id, name="Area Propia", slug="area-propia"),
        Area(organization_id=ajena.id, name="Area Ajena", slug="area-ajena"),
        Area(organization_id=None, name="Area Global", slug="area-global"),
    ])
    db.commit()

    res = http_client.get(f"{API}/areas", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200, res.text

    nombres = {a["name"] for a in res.json()}
    assert "Area Propia" in nombres
    assert "Area Global" in nombres, "Los catalogos globales (NULL) deben seguir visibles"
    assert "Area Ajena" not in nombres, "Fuga entre tenants en /areas"


def test_project_types_muestra_propios_y_globales_pero_no_ajenos(
    db, http_client, admin_token, seed_data
):
    propia = seed_data["org"]
    ajena = _other_org(db)

    db.add_all([
        ProjectType(organization_id=propia.id, name="Tipo Propio", slug="tipo-propio"),
        ProjectType(organization_id=ajena.id, name="Tipo Ajeno", slug="tipo-ajeno"),
        ProjectType(organization_id=None, name="Tipo Global", slug="tipo-global"),
    ])
    db.commit()

    res = http_client.get(
        f"{API}/project-types", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200, res.text

    nombres = {t["name"] for t in res.json()}
    assert "Tipo Propio" in nombres
    assert "Tipo Global" in nombres
    assert "Tipo Ajeno" not in nombres, "Fuga entre tenants en /project-types"


def test_catalogos_exigen_autenticacion(http_client):
    for ruta in ("/products", "/areas", "/project-types"):
        res = http_client.get(f"{API}{ruta}")
        assert res.status_code in (401, 403), f"{ruta} respondio {res.status_code} sin token"
