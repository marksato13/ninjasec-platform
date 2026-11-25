output "public_ip" {
  description = "IP publica de la maquina nueva."
  value       = oci_core_instance.arm.public_ip
}

output "instance_id" {
  description = "OCID de la maquina."
  value       = oci_core_instance.arm.id
}
