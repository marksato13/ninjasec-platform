# Detiene el stack Y BORRA LOS VOLUMENES.
#
# Antes este archivo ejecutaba `docker compose down -v` directamente, sin
# preguntar nada. Un doble clic por error se llevaba la base de datos entera,
# y no hay copia de seguridad automatica todavia.
#
# AGENTS.md lo dice explicitamente: no ejecutar `docker compose down -v`
# sobre una base con datos sin autorizacion y respaldo comprobado. Esta
# confirmacion es esa autorizacion.

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  BORRAR LA BASE DE DATOS LOCAL" -ForegroundColor Red
Write-Host "  -----------------------------" -ForegroundColor DarkRed
Write-Host "  Esto ejecuta 'docker compose down -v' y borra los volumenes."
Write-Host "  TODOS los datos locales se pierden. No hay deshacer." -ForegroundColor Red
Write-Host ""
Write-Host "  Escribe BORRAR para confirmar. Cualquier otra cosa cancela." -ForegroundColor Yellow
$respuesta = Read-Host "  "

if ($respuesta -cne "BORRAR") {
    Write-Host "  Cancelado. No se toco nada." -ForegroundColor Green
    exit 0
}

Set-Location "$PSScriptRoot\infra"
docker compose -p ninjasec down -v
Write-Host "  Volumenes borrados. Al levantar de nuevo, la base arranca vacia." -ForegroundColor Yellow
