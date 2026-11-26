"""Pruebas unitarias para app/core/fases.py"""

import pytest

from app.core import fases


def test_es_valida_devuelve_true_para_claves_validas():
    """test_es_valida_devuelve_true_para_claves_validas"""
    for clave in fases.CLAVES:
        assert fases.es_valida(clave) is True


def test_es_valida_devuelve_false_para_claves_invalidas():
    """test_es_valida_devuelve_false_para_claves_invalidas"""
    invalidas = ["", "otra", "Diagnostico"]
    for clave in invalidas:
        assert fases.es_valida(clave) is False


def test_indice_devuelve_posicion_correcta():
    """test_indice_devuelve_posicion_correcta"""
    esperados = [
        ("diagnostico", 0),
        ("planificacion", 1),
        ("implementacion", 2),
        ("transferencia", 3),
        ("acompanamiento", 4)
    ]
    for clave, posicion in esperados:
        assert fases.indice(clave) == posicion


def test_indice_devuelve_cero_para_clave_desconocida():
    """test_indice_devuelve_cero_para_clave_desconocida"""
    assert fases.indice("") == 0
    assert fases.indice("otra") == 0
    assert fases.indice("Diagnostico") == 0


@pytest.mark.parametrize("categoria", ["desarrollo", "Desarrollo"])
def test_linea_de_devuelve_dev_para_desarrollo(categoria):
    assert fases.linea_de(categoria) == "dev"


@pytest.mark.parametrize("categoria", [None, "", "infraestructura", "nube", "seguridad"])
def test_linea_de_devuelve_infra_para_otras_categorias(categoria):
    assert fases.linea_de(categoria) == "infra"


def test_ROTULOS_tiene_las_lineas_correctas():
    """test_ROTULOS_tiene_las_lineas_correctas"""
    assert set(fases.ROTULOS.keys()) == {"dev", "infra"}


def test_ROTULOS_tiene_claves_correctas():
    """test_ROTULOS_tiene_claves_correctas"""
    for linea in fases.ROTULOS.values():
        assert set(linea.keys()) == set(fases.CLAVES)


def test_ROTULOS_tiene_valores_correctos():
    """test_ROTULOS_tiene_valores_correctos"""
    for linea, claves in fases.ROTULOS.items():
        for clave, (rotulo, descripcion) in claves.items():
            assert isinstance(rotulo, str)
            assert isinstance(descripcion, str)
            assert rotulo != ""
            assert descripcion != ""
"""Pruebas unitarias para app/core/fases.py"""
