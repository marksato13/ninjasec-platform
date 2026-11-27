import typing
from app.db.models import client_system as modelo
from app.modules.client_systems import router


def test_estados_sistema_coherentes():
    """Verifica que los estados del sistema en la API coincidan con los del modelo."""
    assert typing.get_args(router.Estado) == modelo.ESTADOS_SISTEMA


def test_planes_soporte_coherentes():
    """Verifica que los planes de soporte en la API coincidan con los del modelo."""
    assert typing.get_args(router.Plan) == modelo.PLANES_SOPORTE


def test_tipos_entorno_coherentes():
    """Verifica que los tipos de entorno en la API coincidan con los del modelo."""
    assert typing.get_args(router.Tipo) == modelo.TIPOS_ENTORNO


def test_funcion_en_trabaja_correctamente():
    """Verifica que la función _en genere las restricciones CHECK correctamente."""
    assert modelo._en(("a", "b")) == "'a', 'b'"
    assert modelo._en(("x",)) == "'x'"


def test_no_hay_valores_repetidos():
    """Verifica que ninguna de las tuplas tenga valores repetidos."""
    assert len(modelo.ESTADOS_SISTEMA) == len(set(modelo.ESTADOS_SISTEMA))
    assert len(modelo.PLANES_SOPORTE) == len(set(modelo.PLANES_SOPORTE))
    assert len(modelo.TIPOS_ENTORNO) == len(set(modelo.TIPOS_ENTORNO))
