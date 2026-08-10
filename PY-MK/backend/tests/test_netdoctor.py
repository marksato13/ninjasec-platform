"""28-P1: catálogo NetDoctor y modo guiado (árbol de decisión declarativo)."""

from app.db.seed import seed_netdoctor_catalog
from app.modules.netdoctor.guided_tree import GUIDED_TREE

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_catalogo_tiene_14_problemas_con_comandos_por_vendor(db, http_client, admin_token):
    seed_netdoctor_catalog(db)
    response = http_client.get(f"{API}/netdoctor/issues", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    issues = response.json()
    assert len(issues) == 14
    for issue in issues:
        assert set(issue["diagnostic_commands"].keys()) >= {"cisco_ios", "mikrotik", "huawei", "ubiquiti"}


def test_filtro_por_categoria(db, http_client, admin_token):
    seed_netdoctor_catalog(db)
    response = http_client.get(f"{API}/netdoctor/issues?category=VLAN", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    issues = response.json()
    assert len(issues) > 0
    assert all(i["category"] == "VLAN" for i in issues)


def test_obtener_un_problema_por_codigo(db, http_client, admin_token):
    seed_netdoctor_catalog(db)
    response = http_client.get(f"{API}/netdoctor/issues/nd-stploop", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    assert response.json()["code"] == "ND-STPLOOP"


def test_codigo_inexistente_devuelve_404(db, http_client, admin_token):
    seed_netdoctor_catalog(db)
    response = http_client.get(f"{API}/netdoctor/issues/ND-NOEXISTE", headers=_auth(admin_token))
    assert response.status_code == 404


def test_arbol_guiado_es_consistente_con_el_catalogo(db, http_client, admin_token):
    """Cada hoja del árbol apunta a un código real del catálogo, y cada
    'next' apunta a un nodo real del árbol -- sin referencias rotas."""
    seed_netdoctor_catalog(db)
    catalog_response = http_client.get(f"{API}/netdoctor/issues", headers=_auth(admin_token))
    catalog_codes = {i["code"] for i in catalog_response.json()}

    tree_response = http_client.get(f"{API}/netdoctor/guided-tree", headers=_auth(admin_token))
    assert tree_response.status_code == 200, tree_response.text
    tree = tree_response.json()

    leaf_codes = set()
    for node_id, node in tree.items():
        if node.get("issue_code"):
            leaf_codes.add(node["issue_code"])
            assert node["issue_code"] in catalog_codes, f"{node_id} apunta a un código inexistente"
        elif node.get("options"):
            for option in node["options"]:
                assert option["next"] in tree, f"{node_id} apunta a un nodo inexistente"
        else:
            raise AssertionError(f"{node_id} no tiene ni issue_code ni options")

    assert leaf_codes == catalog_codes, "el árbol no cubre exactamente el catálogo completo"


def test_arbol_guiado_python_es_consistente(db):
    """Mismo chequeo, pero directo sobre la estructura Python (no vía HTTP)
    para que un typo en el árbol falle la suite incluso si el catálogo
    todavía no fue sembrado en este test en particular."""
    seed_netdoctor_catalog(db)
    from sqlalchemy import select
    from app.db.models.netdoctor import NetdoctorIssue

    codes = set(db.scalars(select(NetdoctorIssue.code)))
    leaf_codes = set()
    for node_id, node in GUIDED_TREE.items():
        if "issue_code" in node:
            leaf_codes.add(node["issue_code"])
            assert node["issue_code"] in codes
        elif "options" in node:
            for option in node["options"]:
                assert option["next"] in GUIDED_TREE
        else:
            raise AssertionError(f"{node_id} sin issue_code ni options")
    assert leaf_codes == codes
