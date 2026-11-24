# NinjaSec — consola de control
#
# Levanta, detiene y diagnostica el stack local. Pensado para lanzarse desde
# el acceso directo del escritorio, sin recordar ningun comando.
#
#   pwsh -File "PY-MK\ninjasec.ps1"
#
# Tres cosas que este script resuelve y que antes fallaban:
#
#  1. Si Docker Desktop esta cerrado, lo arranca y espera. Era el fallo mas
#     comun: todas las opciones reventaban con un error de npipe que no
#     explicaba nada.
#  2. El `-p ninjasec` va SIEMPRE. Sin el, Compose deriva el nombre del
#     proyecto de la carpeta (`infra`) y levanta un stack paralelo con
#     volumenes vacios: parece que la base de datos se perdio, cuando lo que
#     pasa es que estas mirando otra.
#  3. Borrar la base de datos exige escribir BORRAR. Antes era la opcion 7,
#     a una tecla de la 6 que solo mostraba el estado.

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$PROYECTO   = "ninjasec"
$INFRA      = Join-Path $PSScriptRoot "infra"
$FRONTEND   = "http://localhost:3018"
$BACKEND    = "http://localhost:8024"
$DOCKER_EXE = "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# ---------------------------------------------------------------- utilidades

function Write-Titulo([string]$texto) {
    Write-Host ""
    Write-Host "  $texto" -ForegroundColor Cyan
    Write-Host "  $('-' * $texto.Length)" -ForegroundColor DarkCyan
}

function Write-Ok    ([string]$t) { Write-Host "  [OK] $t" -ForegroundColor Green }
function Write-Mal   ([string]$t) { Write-Host "  [!!] $t" -ForegroundColor Red }
function Write-Aviso ([string]$t) { Write-Host "  [ * ] $t" -ForegroundColor Yellow }
function Write-Gris  ([string]$t) { Write-Host "       $t" -ForegroundColor DarkGray }

function Test-Docker {
    try {
        docker version --format '{{.Server.Version}}' 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    } catch { return $false }
}

function Confirm-Docker {
    # Devuelve $true si el demonio responde. Si no, arranca Docker Desktop y
    # espera hasta 3 minutos.
    if (Test-Docker) { return $true }

    Write-Aviso "Docker Desktop no esta corriendo."
    if (-not (Test-Path $DOCKER_EXE)) {
        Write-Mal "Tampoco lo encuentro en: $DOCKER_EXE"
        Write-Gris "Arrancalo a mano y vuelve a intentarlo."
        return $false
    }

    Write-Host "  Arrancandolo" -NoNewline
    Start-Process $DOCKER_EXE | Out-Null

    foreach ($i in 1..36) {
        Start-Sleep -Seconds 5
        Write-Host "." -NoNewline
        if (Test-Docker) {
            Write-Host ""
            Write-Ok "Docker listo tras $($i * 5) segundos."
            return $true
        }
    }
    Write-Host ""
    Write-Mal "Docker no respondio en 3 minutos. Revisa Docker Desktop."
    return $false
}

function Invoke-Compose {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Argumentos)
    Push-Location $INFRA
    try { & docker compose -p $PROYECTO @Argumentos }
    finally { Pop-Location }
}

function Test-Url([string]$url, [int]$timeout = 8) {
    try {
        $r = Invoke-WebRequest -Uri $url -TimeoutSec $timeout -UseBasicParsing -ErrorAction Stop
        return [int]$r.StatusCode
    } catch {
        if ($_.Exception.Response) { return [int]$_.Exception.Response.StatusCode }
        return 0
    }
}

function Wait-Stack {
    # Espera a que backend y frontend respondan DE VERDAD. Que compose
    # termine sin error no significa que la aplicacion este lista.
    Write-Host "  Esperando a que responda" -NoNewline
    $backendOk = $false
    $frontendOk = $false

    foreach ($i in 1..40) {
        if (-not $backendOk)  { $backendOk  = (Test-Url "$BACKEND/health" 3) -eq 200 }
        if (-not $frontendOk) { $frontendOk = (Test-Url $FRONTEND 3) -eq 200 }
        if ($backendOk -and $frontendOk) { break }
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 3
    }
    Write-Host ""

    if ($backendOk) { Write-Ok "Backend  $BACKEND" } else { Write-Mal "Backend no responde" }
    if ($frontendOk) { Write-Ok "Frontend $FRONTEND" } else { Write-Mal "Frontend no responde" }

    if (-not ($backendOk -and $frontendOk)) {
        Write-Gris "Usa la opcion D (depurar) para ver que pasa."
    }
    return ($backendOk -and $frontendOk)
}

# ------------------------------------------------------------------ acciones

function Invoke-Levantar {
    param([switch]$Reconstruir)

    if (-not (Confirm-Docker)) { return }
    if ($Reconstruir) { Write-Titulo "Levantando con reconstruccion" }
    else { Write-Titulo "Levantando" }

    if ($Reconstruir) { Invoke-Compose up -d --build } else { Invoke-Compose up -d }
    if ($LASTEXITCODE -ne 0) {
        Write-Mal "Compose fallo."
        if (-not (Test-Path (Join-Path $INFRA ".env"))) {
            # Causa numero uno, y el mensaje de Compose no la nombra: dice
            # "required variable POSTGRES_PASSWORD is missing" sin decir que
            # falta el archivo entero. Pasa al lanzar esto desde un worktree,
            # porque .env esta en .gitignore y solo existe en el checkout real.
            Write-Mal "No existe $INFRA\.env"
            Write-Gris "Copialo desde infra/.env.example y rellena los valores."
            Write-Gris "Si lanzaste esto desde un worktree de git, usa el repo principal."
        } else {
            Write-Gris "Usa la opcion D para ver por que."
        }
        return
    }

    if (Wait-Stack) {
        Write-Host ""
        Write-Host "  Listo. " -NoNewline -ForegroundColor Green
        Write-Host "$FRONTEND/dashboard"
    }
}

function Invoke-Detener {
    if (-not (Confirm-Docker)) { return }
    Write-Titulo "Deteniendo"
    Write-Gris "Los datos se conservan: esto no toca los volumenes."
    Invoke-Compose down
    Write-Ok "Detenido."
}

function Invoke-Reiniciar {
    if (-not (Confirm-Docker)) { return }
    Write-Titulo "Reiniciando"
    Invoke-Compose restart
    Wait-Stack | Out-Null
}

function Show-Estado {
    if (-not (Confirm-Docker)) { return }
    Write-Titulo "Estado"
    Invoke-Compose ps
}

function Show-Logs {
    if (-not (Confirm-Docker)) { return }
    Write-Titulo "Logs"
    Write-Host "  1) todo    2) backend    3) frontend    4) postgres" -ForegroundColor DarkGray
    $cual = Read-Host "  Cual"
    $svc = switch ($cual) {
        "2" { "backend" }
        "3" { "frontend" }
        "4" { "postgres" }
        default { $null }
    }
    Write-Gris "Ctrl+C para salir."
    if ($svc) { Invoke-Compose logs -f --tail 100 $svc }
    else { Invoke-Compose logs -f --tail 100 }
}

function Invoke-Depurar {
    Write-Titulo "Diagnostico"

    # 1. Docker
    if (Test-Docker) {
        Write-Ok "Docker $(docker version --format '{{.Server.Version}}')"
    } else {
        Write-Mal "Docker Desktop no responde. Todo lo demas va a fallar."
        Write-Gris "Usa la opcion 1: lo arranca solo."
        return
    }

    # 2. Contenedores
    Write-Host ""
    Write-Host "  Contenedores" -ForegroundColor White
    $filas = docker ps -a --filter "label=com.docker.compose.project=$PROYECTO" --format '{{.Names}}|{{.State}}|{{.Status}}' 2>$null
    if (-not $filas) {
        Write-Mal "Ninguno. El stack no esta levantado: usa la opcion 1."
    } else {
        foreach ($f in $filas) {
            $p = $f -split '\|', 3
            if ($p[1] -eq 'running' -and $p[2] -notmatch 'unhealthy') { Write-Ok "$($p[0])  $($p[2])" }
            else { Write-Mal "$($p[0])  $($p[1]) - $($p[2])" }
        }
    }

    # 3. Proyectos paralelos: el error que ya ocurrio una vez
    $otros = docker ps -a --format '{{.Label "com.docker.compose.project"}}' 2>$null |
             Where-Object { $_ -and $_ -ne $PROYECTO -and $_ -match 'ninjasec|infra' } |
             Select-Object -Unique
    if ($otros) {
        Write-Host ""
        Write-Aviso "Hay contenedores de OTRO proyecto de Compose: $($otros -join ', ')"
        Write-Gris "Suele pasar al lanzar 'docker compose up' sin el -p ninjasec."
        Write-Gris "Tienen volumenes distintos: parece que la base se perdio y no es asi."
    }

    # 4. Puertos
    Write-Host ""
    Write-Host "  Respuestas HTTP" -ForegroundColor White
    $destinos = @(
        @{ n = "Frontend";  u = $FRONTEND },
        @{ n = "Dashboard"; u = "$FRONTEND/dashboard" },
        @{ n = "Backend";   u = "$BACKEND/health" },
        @{ n = "Swagger";   u = "$BACKEND/docs" }
    )
    foreach ($d in $destinos) {
        $c = Test-Url $d.u
        $estado = if ($c) { "$c" } else { "sin respuesta" }
        $txt = "{0,-10} {1,-42} {2}" -f $d.n, $d.u, $estado
        if ($c -eq 200) { Write-Ok $txt } else { Write-Mal $txt }
    }

    # 5. Capsulas
    try {
        $caps = Invoke-RestMethod -Uri "$BACKEND/api/v1/capsulas" -TimeoutSec 8 -ErrorAction Stop
        Write-Host ""
        Write-Host "  Capsulas de funcionalidad" -ForegroundColor White
        foreach ($c in $caps.capsulas) {
            if ($c.activa) {
                Write-Ok "$($c.nombre): encendida"
            } else {
                Write-Gris "$($c.nombre): apagada"
                Write-Gris "  motivo: $($c.motivo)"
            }
        }
    } catch {
        # Sin backend no hay capsulas que listar; ya se reporto arriba.
    }

    # 6. Base de datos
    Write-Host ""
    Write-Host "  Base de datos" -ForegroundColor White
    $sql = "select 'usuarios='||(select count(*) from users)||'  clientes='||(select count(*) from clients)||'  proyectos='||(select count(*) from projects);"
    $conteo = docker exec "$PROYECTO-postgres" psql -U postgres -d ninjasec -tAc $sql 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Ok "$($conteo -join '')".Trim() }
    else { Write-Mal "No pude consultar la base." }

    $rev = docker exec "$PROYECTO-postgres" psql -U postgres -d ninjasec -tAc "select version_num from alembic_version;" 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Ok "Migracion aplicada: $("$rev".Trim())" }

    # 7. Errores recientes
    Write-Host ""
    Write-Host "  Errores recientes en los logs" -ForegroundColor White
    $hubo = $false
    foreach ($svc in @("backend", "frontend", "postgres")) {
        $errs = docker logs "$PROYECTO-$svc" --tail 200 2>&1 |
                Select-String -Pattern 'ERROR|CRITICAL|Traceback|FATAL' |
                Select-Object -Last 3
        if ($errs) {
            $hubo = $true
            Write-Mal "${svc}:"
            foreach ($e in $errs) { Write-Gris "$e".Trim() }
        }
    }
    if (-not $hubo) { Write-Ok "Ninguno en las ultimas 200 lineas." }
    Write-Host ""
}

function Invoke-Sembrar {
    if (-not (Confirm-Docker)) { return }
    Write-Titulo "Sembrar datos"
    Write-Host "  1) Planes de estudio (NSE 4 y CCNA)" -ForegroundColor DarkGray
    Write-Host "  2) Datos de demostracion peruanos" -ForegroundColor DarkGray
    $cual = Read-Host "  Cual"

    if ($cual -eq "1") {
        docker exec "$PROYECTO-backend" python -m app.db.seed_planes_estudio
        if ($LASTEXITCODE -eq 0) { Write-Ok "Planes de estudio sembrados." }
    }
    elseif ($cual -eq "2") {
        Write-Aviso "Anade clientes y dispositivos de ejemplo a la base actual."
        if ((Read-Host "  Seguro? (s/n)") -eq "s") {
            docker exec "$PROYECTO-backend" python /app/seed_demo.py
        } else { Write-Gris "Cancelado." }
    }
    else { Write-Gris "Cancelado." }
}

function Open-Navegador {
    Write-Titulo "Abrir"
    Write-Host "  1) Panel    2) Portal cliente    3) Swagger" -ForegroundColor DarkGray
    switch (Read-Host "  Cual") {
        "2" { Start-Process "$FRONTEND/portal" }
        "3" { Start-Process "$BACKEND/docs" }
        default { Start-Process "$FRONTEND/dashboard" }
    }
}

function Remove-Datos {
    Write-Titulo "BORRAR LA BASE DE DATOS"
    Write-Mal "Esto ejecuta 'docker compose down -v'."
    Write-Mal "Borra los volumenes: TODOS los datos locales se pierden."
    Write-Gris "No hay deshacer, y no hay copia de seguridad automatica todavia."
    Write-Host ""
    Write-Host "  Escribe BORRAR para confirmar. Cualquier otra cosa cancela." -ForegroundColor Yellow
    $r = Read-Host "  "
    if ($r -cne "BORRAR") { Write-Ok "Cancelado. No se toco nada."; return }

    if (-not (Confirm-Docker)) { return }
    Invoke-Compose down -v
    Write-Aviso "Volumenes borrados. Al levantar de nuevo, la base arranca vacia."
}

# ---------------------------------------------------------------------- menu

function Show-Menu {
    Write-Host ""
    Write-Host "  ===========================================" -ForegroundColor DarkCyan
    Write-Host "            N I N J A S E C                 " -ForegroundColor Cyan
    Write-Host "  ===========================================" -ForegroundColor DarkCyan
    Write-Host ""
    Write-Host "   1  Levantar" -ForegroundColor Green
    Write-Host "   2  Levantar reconstruyendo " -NoNewline -ForegroundColor Green
    Write-Host "(tras cambiar codigo)" -ForegroundColor DarkGray
    Write-Host "   3  Detener                 " -NoNewline
    Write-Host "(conserva los datos)" -ForegroundColor DarkGray
    Write-Host "   4  Reiniciar"
    Write-Host ""
    Write-Host "   E  Estado"
    Write-Host "   L  Logs"
    Write-Host "   D  Depurar                 " -NoNewline -ForegroundColor Yellow
    Write-Host "(que falla y por que)" -ForegroundColor DarkGray
    Write-Host "   S  Sembrar datos"
    Write-Host "   A  Abrir en el navegador"
    Write-Host ""
    Write-Host "   X  Borrar la base de datos  " -NoNewline -ForegroundColor Red
    Write-Host "(pide confirmacion escrita)" -ForegroundColor DarkGray
    Write-Host "   0  Salir"
    Write-Host ""
}

$salir = $false
while (-not $salir) {
    Show-Menu
    $opcion = (Read-Host "  Opcion").Trim().ToUpper()

    switch ($opcion) {
        "1" { Invoke-Levantar }
        "2" { Invoke-Levantar -Reconstruir }
        "3" { Invoke-Detener }
        "4" { Invoke-Reiniciar }
        "E" { Show-Estado }
        "L" { Show-Logs }
        "D" { Invoke-Depurar }
        "S" { Invoke-Sembrar }
        "A" { Open-Navegador }
        "X" { Remove-Datos }
        "0" { $salir = $true }
        default { Write-Aviso "Opcion no valida." }
    }

    if (-not $salir) {
        Write-Host ""
        Write-Host "  Pulsa Enter para volver al menu..." -ForegroundColor DarkGray
        Read-Host | Out-Null
        Clear-Host
    }
}
