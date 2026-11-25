terraform {
  required_version = ">= 1.6"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0, < 8.0"
    }
  }
}

# La autenticacion sale de ~/.oci/config (perfil DEFAULT). Nada de claves en este repositorio.
provider "oci" {
  auth                = "ApiKey"
  config_file_profile = "DEFAULT"
  region              = var.region
}
