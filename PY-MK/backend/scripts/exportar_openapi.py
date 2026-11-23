"""Vuelca el esquema OpenAPI de la API a un archivo JSON.

Para que el CI pueda comparar el contrato de un PR contra el de la rama
destino y avisar si un cambio rompe a quien lo consume.

Se genera por IMPORTACION, no levantando el servidor: `app.openapi()` no
necesita base de datos ni red, porque el `lifespan` solo corre al arrancar
uvicorn. Eso hace que el job del CI tarde segundos en vez de minutos y que
no dependa de que Docker levante.

Uso:
    PYTHONPATH=. python scripts/exportar_openapi.py openapi.json
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Valores minimos para que Settings valide al importar. No son secretos:
# este script no abre conexiones, solo construye el objeto FastAPI para
# leer su esquema.
os.environ.setdefault("JWT_SECRET_KEY", "solo-para-exportar-el-esquema")
os.environ.setdefault("SEED_ON_STARTUP", "false")
os.environ.setdefault("APP_ENV", "development")

# TODAS las capsulas encendidas al exportar.
#
# El contrato describe lo que OFRECE EL CODIGO, no lo que sirve un despliegue
# concreto. Si el esquema siguiera al interruptor, apagar una capsula se leeria
# como la desaparicion de 13 rutas -- un cambio rompedor-- y el check empezaria
# a gritar cada vez que se toca una variable de entorno. Eso lo convierte en
# ruido, y un check que grita por todo deja de cazar las roturas de verdad.
#
# Que un despliegue con una capsula apagada sirva un subconjunto del contrato
# esta documentado en DOCUMENTOS/ESTRATEGIA/10-MODULOS-ACTIVABLES.md. Es
# configuracion de despliegue, no una incompatibilidad de la API.
#
# Se construye desde el registro para que una capsula nueva entre sola.
from app.core.features import CAPSULAS  # noqa: E402

os.environ["CAPSULAS_ACTIVAS"] = ",".join(sorted(CAPSULAS))


def main() -> int:
    destino = Path(sys.argv[1] if len(sys.argv) > 1 else "openapi.json")

    from app.main import app

    esquema = app.openapi()

    # La version se excluye del contrato a proposito: subir APP_VERSION no
    # es un cambio incompatible y no debe teñir el diff.
    esquema.get("info", {}).pop("version", None)

    destino.write_text(
        json.dumps(esquema, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )

    rutas = len(esquema.get("paths", {}))
    esquemas = len(esquema.get("components", {}).get("schemas", {}))
    print(
        f"Escrito {destino}: {rutas} rutas, {esquemas} esquemas "
        f"(capsulas: {os.environ['CAPSULAS_ACTIVAS'] or 'ninguna'})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
