<#
.SYNOPSIS
  Reintenta `terraform apply` hasta que Oracle tenga hueco para la maquina ARM gratuita.

.DESCRIPTION
  Oracle responde "Out of host capacity" casi siempre en la region de Santiago. Este bucle lo
  repite con pausa y azar hasta que se crea, y se detiene solo.

  - Corre en tu PC, FUERA de Claude: no gasta tokens.
  - Solo reintenta ante falta de capacidad o limite de peticiones. Cualquier otro error PARA el
    bucle y lo dice, porque repetirlo no lo arreglaria.
  - Antes de cada ronda comprueba si la maquina ya existe en el estado de Terraform.

.EXAMPLE
  .\reintentar.ps1                       # bucle
  .\reintentar.ps1 -UnaVez               # una sola ronda, para probar
#>
[CmdletBinding()]
param(
  [string]$VarFile  = (Join-Path $HOME '.oci\terraform\arm.tfvars'),
  [string]$StateDir = (Join-Path $HOME '.oci\terraform'),
  [int]$EsperaMin   = 5,
  [int]$EsperaMax   = 12,
  [int]$EsperaLimite = 20,
  [switch]$UnaVez
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$log = Join-Path $StateDir 'reintentar.log'
$state = Join-Path $StateDir 'arm.tfstate'
$env:TF_DATA_DIR = Join-Path $StateDir '.terraform-data'
$env:TF_IN_AUTOMATION = '1'

function Escribir($m) {
  $l = '[{0:yyyy-MM-dd HH:mm:ss}] {1}' -f (Get-Date), $m
  Write-Host $l
  Add-Content -Path $log -Value $l -Encoding utf8
}

if (-not (Test-Path $VarFile)) { throw "Falta $VarFile (copia terraform.tfvars.example y rellenalo)." }
if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) { throw 'terraform no esta en el PATH.' }

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
Escribir 'inicio: terraform init'
terraform init -input=false -upgrade=false | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'terraform init fallo' }
terraform validate | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'terraform validate fallo' }

$ronda = 0
while ($true) {
  $ronda++
  $existe = terraform state list -state="$state" 2>$null | Select-String 'oci_core_instance.arm'
  if ($existe) { Escribir 'La maquina ya esta en el estado de Terraform. Fin.'; break }

  $salida = terraform apply -auto-approve -input=false -no-color -state="$state" -var-file="$VarFile" 2>&1 | Out-String
  if ($LASTEXITCODE -eq 0) {
    Escribir "CREADA en la ronda $ronda."
    terraform output -state="$state" -no-color | ForEach-Object { Escribir $_ }
    break
  }

  if ($salida -match '(?i)out of (host )?capacity|OutOfHostCapacity') {
    $espera = Get-Random -Minimum $EsperaMin -Maximum ($EsperaMax + 1)
    Escribir "ronda ${ronda}: sin capacidad. Espero $espera min."
  } elseif ($salida -match '(?i)429|too many requests|TooManyRequests') {
    $espera = $EsperaLimite
    Escribir "ronda ${ronda}: Oracle limita las peticiones. Espero $espera min."
  } else {
    Escribir "ERROR NO REINTENTABLE (ronda $ronda). Detengo el bucle. Salida:"
    $salida.Trim() -split "`n" | Select-Object -First 25 | ForEach-Object { Escribir "  $_" }
    exit 2
  }

  if ($UnaVez) { break }
  Start-Sleep -Seconds ($espera * 60)
}
