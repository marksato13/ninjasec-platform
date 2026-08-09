"""Verificaciones de documentos renombrados fuera del código de la aplicación."""

from __future__ import annotations

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
FIX_DIRECTORY = REPOSITORY_ROOT / "DOCUMENTOS" / "PLATAFORMA" / "FIX"
INVENTORY_FIX = FIX_DIRECTORY / "FIX-INVENTARIO-PRIMERO-SIN-INTEGRACION.md"


def test_inventory_fix_with_correct_extension_is_valid_github_markdown():
    """El reemplazo de G-05 conserva un documento Markdown renderizable."""
    content = INVENTORY_FIX.read_text(encoding="utf-8")
    lines = content.splitlines()

    assert lines[0].startswith("# ")
    assert "## Objetivo" in lines
    assert "## Implementacion realizada" in lines
    assert "## Resultado funcional" in lines
    assert "## Nota importante" in lines

    # GitHub interpreta los elementos de estas listas como Markdown; cada
    # elemento debe conservar su marcador para no degradarse a texto plano.
    assert any(line.startswith("1. ") for line in lines)
    assert any(line.startswith("- ") for line in lines)

    # Un número impar de delimitadores de bloque rompería el resto del render.
    assert sum(line.startswith("```") for line in lines) % 2 == 0
