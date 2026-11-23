# estado.ps1 - Lectura rapida del estado de NinjaSec.
# Solo lee. No commitea, no fusiona, no crea ramas.
#
# [LAPTOP PowerShell] -> pwsh -File "CORTEX\herramientas\estado.ps1"

[CmdletBinding()]
param(
    [switch]$SinRed   # omite las consultas a GitHub
)

$ErrorActionPreference = 'Stop'

$principal = "C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\EMPRESA NINJA-SEC"

function Write-Titulo([string]$texto) {
    Write-Host ""
    Write-Host "== $texto " -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * [Math]::Max(0, 60 - $texto.Length)) -ForegroundColor DarkCyan
}

if (-not (Test-Path $principal)) {
    Write-Host "No encuentro el repo en: $principal" -ForegroundColor Red
    exit 1
}

Push-Location $principal
try {
    # ---------------------------------------------------------------- atraso
    Write-Titulo "Atraso de main"
    if (-not $SinRed) { git fetch --prune origin 2>$null | Out-Null }

    $local  = (git rev-parse --short HEAD).Trim()
    $remoto = (git rev-parse --short origin/main 2>$null)
    if ($remoto) {
        $remoto  = $remoto.Trim()
        $detras  = @(git rev-list --count "HEAD..origin/main" 2>$null)[0]
        if ($local -eq $remoto) {
            Write-Host "  main local al dia ($local)" -ForegroundColor Green
        } else {
            Write-Host "  local $local  <->  origin/main $remoto  ($detras commits detras)" -ForegroundColor Yellow
            Write-Host "  Ramifica SIEMPRE desde origin/main, no desde el main local." -ForegroundColor DarkYellow
        }
    }

    # ------------------------------------------------------------- worktrees
    Write-Titulo "Worktrees"
    $lineas = git worktree list --porcelain
    $rutas  = @()
    foreach ($l in $lineas) {
        if ($l -like 'worktree *') { $rutas += $l.Substring(9) }
    }

    $sucios = 0
    foreach ($ruta in $rutas) {
        $rama = (git -C $ruta branch --show-current 2>$null)
        if (-not $rama) { $rama = '(detached)' }
        $cambios = @(git -C $ruta status --short 2>$null)
        $nombre  = Split-Path $ruta -Leaf

        if ($cambios.Count -gt 0) {
            $sucios++
            Write-Host ("  {0,-28} {1,-38} {2} cambios sin commitear" -f $nombre, $rama, $cambios.Count) -ForegroundColor Yellow
        } else {
            Write-Host ("  {0,-28} {1}" -f $nombre, $rama) -ForegroundColor DarkGray
        }
    }
    Write-Host ("  -> {0} worktrees, {1} con trabajo sin guardar" -f $rutas.Count, $sucios)

    if (-not $SinRed) {
        # --------------------------------------------------------------- PRs
        Write-Titulo "PR abiertos propios"
        $prs = gh pr list --author "@me" --json number,title,mergeable,headRefName | ConvertFrom-Json
        if (-not $prs -or $prs.Count -eq 0) {
            Write-Host "  ninguno" -ForegroundColor DarkGray
        } else {
            foreach ($pr in $prs) {
                $color = if ($pr.mergeable -eq 'MERGEABLE') { 'Green' } else { 'Yellow' }
                Write-Host ("  #{0,-5} [{1,-10}] {2}" -f $pr.number, $pr.mergeable, $pr.title) -ForegroundColor $color

                $checks = gh pr checks $pr.number --json name,state 2>$null | ConvertFrom-Json
                if ($checks) {
                    $rojos = @($checks | Where-Object { $_.state -in @('FAILURE','ERROR','CANCELLED') })
                    $curso = @($checks | Where-Object { $_.state -in @('PENDING','IN_PROGRESS','QUEUED') })
                    if ($rojos.Count -gt 0) {
                        foreach ($r in $rojos) { Write-Host ("         ROJO: {0}" -f $r.name) -ForegroundColor Red }
                    } elseif ($curso.Count -gt 0) {
                        Write-Host ("         {0} checks en curso" -f $curso.Count) -ForegroundColor DarkYellow
                    } else {
                        Write-Host "         todos los checks en verde" -ForegroundColor DarkGreen
                    }
                }
            }
        }

        # -------------------------------------------------------- dependabot
        Write-Titulo "Dependabot"
        $dep = gh pr list --author app/dependabot --json number | ConvertFrom-Json
        $n = if ($dep) { $dep.Count } else { 0 }
        $color = if ($n -gt 10) { 'Yellow' } else { 'DarkGray' }
        Write-Host ("  {0} PR abiertos sin triar" -f $n) -ForegroundColor $color
    }

    # ------------------------------------------------------------ recordator
    Write-Titulo "Bloquea el despliegue publico"
    Write-Host "  1. Contrasenas del seed en texto plano        -> Claude" -ForegroundColor Red
    Write-Host "  2. Rotar los secretos G-03                    -> MARK" -ForegroundColor Red
    Write-Host "  3. Copias de seguridad de Postgres            -> Claude" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Detalle: CORTEX\40-TAREAS\Tablero.md" -ForegroundColor DarkGray
    Write-Host "  Enrutado: CORTEX\10-ENRUTADO\Politica-de-enrutado.md" -ForegroundColor DarkGray
    Write-Host ""
}
finally {
    Pop-Location
}
