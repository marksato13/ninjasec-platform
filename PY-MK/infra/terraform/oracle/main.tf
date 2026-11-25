# Maquina ARM gratuita (Always Free) para NinjaSec.
#
# La forma esta FIJA a VM.Standard.A1.Flex a proposito: no es una variable, para que ningun
# valor mal puesto cree una maquina de pago. La red (VCN y subred) ya existe y se reutiliza.

resource "oci_core_instance" "arm" {
  compartment_id      = var.compartment_id
  availability_domain = var.availability_domain
  display_name        = var.display_name
  shape               = "VM.Standard.A1.Flex"

  shape_config {
    ocpus         = var.ocpus
    memory_in_gbs = var.memory_gbs
  }

  source_details {
    source_type             = "image"
    source_id               = var.image_id
    boot_volume_size_in_gbs = var.boot_volume_gbs
  }

  create_vnic_details {
    subnet_id        = var.subnet_id
    assign_public_ip = true
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
  }

  # Cambiar la imagen o el disco destruiria y recrearia la maquina: se ignora a proposito.
  # Actualizar el sistema operativo se hace dentro de la maquina, no desde aqui.
  lifecycle {
    ignore_changes  = [source_details[0].source_id, metadata]
    prevent_destroy = true
  }
}
