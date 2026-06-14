output "vcn_id" {
  value = oci_core_vcn.this.id
}

output "vcn_cidr" {
  value = oci_core_vcn.this.cidr_block
}

output "public_subnet_id" {
  value = oci_core_subnet.public.id
}

output "private_subnet_id" {
  value = oci_core_subnet.private.id
}

output "data_subnet_id" {
  value = oci_core_subnet.data.id
}

output "public_security_list_id" {
  value = oci_core_security_list.public.id
}

output "private_security_list_id" {
  value = oci_core_security_list.private.id
}

output "data_security_list_id" {
  value = oci_core_security_list.data.id
}

output "nat_gateway_id" {
  value = oci_core_nat_gateway.this.id
}

output "internet_gateway_id" {
  value = oci_core_internet_gateway.this.id
}
