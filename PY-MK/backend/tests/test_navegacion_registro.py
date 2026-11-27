"""Pruebas para las reglas del registro de menús."""

from app.core import navegacion as n
from app.core.features import CAPSULAS


def test_claves_unicas():
    """Claves únicas: len(_POR_CLAVE) == len(OPCIONES)."""
    assert len(n._POR_CLAVE) == len(n.OPCIONES)


def test_opciones_solo_permitidas_a_audiencias_de_superficie():
    """Cada opción solo se permite a audiencias de su superficie."""
    for o in n.OPCIONES:
        assert set(o.permitidas) <= set(n.SUPERFICIES[o.superficie])


def test_obligatoria_para_siempre_dentro_de_permitidas():
    """obligatoria_para siempre está dentro de permitidas."""
    for o in n.OPCIONES:
        assert set(o.obligatoria_para) <= set(o.permitidas)


def test_capsulas_existentes():
    """Toda capsula que no sea None existe en CAPSULAS."""
    for o in n.OPCIONES:
        if o.capsula is not None:
            assert o.capsula in CAPSULAS


def test_opciones_obligatorias():
    """Login es obligatorio para visitor y Configuración para super_admin."""
    assert n.opcion("public", "/login").obligatoria_para == ("visitor",)
    assert n.opcion("staff", "/dashboard/settings").obligatoria_para == ("super_admin",)


def test_opcion_inexistente():
    """Opción inexistente devuelve None."""
    assert n.opcion("staff", "/no-existe") is None


def test_opciones_por_superficie():
    """opciones_de devuelve solo opciones de esa superficie."""
    total = 0
    for superficie in n.SUPERFICIES:
        opciones = n.opciones_de(superficie)
        assert all(o.superficie == superficie for o in opciones)
        total += len(opciones)
    
    assert total == len(n.OPCIONES)


def test_audiencias_y_visibilidad():
    """Audencias y visibilidad de Leads."""
    opcion_leads = n.opcion("staff", "/dashboard/leads")
    assert n.audiencias_de(opcion_leads) == ("super_admin", "admin")
    assert not n.visible_por_defecto(opcion_leads, "collaborator")
    assert n.visible_por_defecto(opcion_leads, "admin")
