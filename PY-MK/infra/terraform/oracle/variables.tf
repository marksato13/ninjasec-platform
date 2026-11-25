variable "region" {
  description = "Region de Oracle Cloud."
  type        = string
  default     = "sa-santiago-1"
}

variable "compartment_id" {
  description = "OCID del compartimento donde se crea la maquina (en cuentas nuevas, el tenancy)."
  type        = string
}

variable "availability_domain" {
  description = "Dominio de disponibilidad, p. ej. xxxx:SA-SANTIAGO-1-AD-1."
  type        = string
}

variable "subnet_id" {
  description = "OCID de una subred PUBLICA existente."
  type        = string
}

variable "image_id" {
  description = "OCID de una imagen Ubuntu aarch64 (ARM) de la region."
  type        = string
}

variable "ssh_public_key" {
  description = "Clave SSH PUBLICA que podra entrar como 'ubuntu'."
  type        = string
}

variable "display_name" {
  description = "Nombre de la maquina."
  type        = string
  default     = "ninjasec-arm"
}

# --- Salvaguardas: esto solo puede crear lo que es gratis para siempre -----------------------
# El limite de Always Free para ARM es 4 OCPU y 24 GB en total, repartidos entre todas las
# maquinas A1 de la cuenta. Con estas validaciones un error de tecleo no genera un cargo.

variable "ocpus" {
  description = "OCPU de la A1. Maximo gratuito: 4 en total."
  type        = number
  default     = 2

  validation {
    condition     = var.ocpus >= 1 && var.ocpus <= 4
    error_message = "Always Free permite como maximo 4 OCPU ARM entre todas las maquinas."
  }
}

variable "memory_gbs" {
  description = "Memoria de la A1 en GB. Maximo gratuito: 24 en total."
  type        = number
  default     = 12

  validation {
    condition     = var.memory_gbs >= 1 && var.memory_gbs <= 24
    error_message = "Always Free permite como maximo 24 GB de memoria ARM entre todas las maquinas."
  }
}

variable "boot_volume_gbs" {
  description = "Disco de arranque en GB. Always Free incluye 200 GB de almacenamiento en bloque en total."
  type        = number
  default     = 100

  validation {
    condition     = var.boot_volume_gbs >= 50 && var.boot_volume_gbs <= 200
    error_message = "El disco debe estar entre 50 y 200 GB para seguir dentro de Always Free."
  }
}
