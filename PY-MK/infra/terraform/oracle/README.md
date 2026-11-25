# Máquina ARM gratuita en Oracle Cloud, con Terraform

Crea **una** máquina `VM.Standard.A1.Flex` (Always Free) reutilizando la red que ya existe.
Sirve para salir de la máquina de pago antes de que caduque el crédito de prueba.

## Qué garantiza

- **No puede crear nada de pago.** La forma está fija en `VM.Standard.A1.Flex` y las variables
  validan los límites gratuitos (4 OCPU, 24 GB, 200 GB de disco).
- **Sin secretos en git.** La autenticación sale de `~/.oci/config`; el `tfvars` y el estado
  viven fuera del repositorio (`~/.oci/terraform/`) y `.gitignore` los excluye.
- **No se destruye por accidente:** `prevent_destroy = true`.

## Uso

```powershell
# 1. Una vez: copia terraform.tfvars.example a ~\.oci\terraform\arm.tfvars y rellénalo.
# 2. Prueba en seco (solo lectura):
terraform plan -state="$HOME\.oci\terraform\arm.tfstate" -var-file="$HOME\.oci\terraform\arm.tfvars"
# 3. Reintenta hasta que Oracle tenga hueco (se detiene solo):
.\reintentar.ps1
```

`reintentar.ps1` corre en tu PC, no en un agente de IA. Reintenta solo ante «sin capacidad» o
límite de peticiones; cualquier otro error detiene el bucle. El registro está en
`~\.oci\terraform\reintentar.log`.

## Después de crearse

La máquina nueva sale vacía. El instalador de la plataforma está en `PY-MK/infra/`
(`instalar.sh` y `activar-despliegue-continuo.sh`). Mover los datos de la máquina actual es un
paso aparte y **no se hace desde aquí**: hay que respaldar la base antes y copiarla a mano.

## Pendiente conocido

- La máquina de pago actual (`ninjasec-pago`) se creó con el SDK y **no** está en este estado.
  Importarla (`terraform import`) es opcional; no hace falta para migrar.
- El estado es local. Con una sola persona basta; si el equipo crece, conviene un backend remoto
  (Object Storage de Oracle, que también es gratuito dentro de los límites).
