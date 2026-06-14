# VCN
resource "oci_core_vcn" "this" {
  compartment_id = var.compartment_ocid
  display_name   = "iicpc-${var.environment}-vcn"
  cidr_block     = var.vcn_cidr
  dns_label      = "iicpc${var.environment}"
  defined_tags   = var.tags
}

# Internet Gateway
resource "oci_core_internet_gateway" "this" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "iicpc-${var.environment}-igw"
  enabled        = true
}

# NAT Gateway
resource "oci_core_nat_gateway" "this" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "iicpc-${var.environment}-nat"
}

# Service Gateway
resource "oci_core_service_gateway" "this" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "iicpc-${var.environment}-sgw"
  services {
    service_id = data.oci_core_services.this.services[0].id
  }
}

data "oci_core_services" "this" {
  filter {
    name   = "name"
    values = ["All.*"]
  }
}

# Public subnet
resource "oci_core_subnet" "public" {
  compartment_id      = var.compartment_ocid
  vcn_id              = oci_core_vcn.this.id
  display_name        = "iicpc-${var.environment}-public"
  cidr_block          = var.public_subnet_cidr
  dns_label           = "public"
  prohibit_public_ip_on_vnic = false
  route_table_id      = oci_core_route_table.public.id
  security_list_ids   = [oci_core_security_list.public.id]
  dhcp_options_id     = oci_core_vcn.this.default_dhcp_options_id
}

# Private subnet
resource "oci_core_subnet" "private" {
  compartment_id      = var.compartment_ocid
  vcn_id              = oci_core_vcn.this.id
  display_name        = "iicpc-${var.environment}-private"
  cidr_block          = var.private_subnet_cidr
  dns_label           = "private"
  prohibit_public_ip_on_vnic = true
  route_table_id      = oci_core_route_table.private.id
  security_list_ids   = [oci_core_security_list.private.id]
  dhcp_options_id     = oci_core_vcn.this.default_dhcp_options_id
}

# Data subnet
resource "oci_core_subnet" "data" {
  compartment_id      = var.compartment_ocid
  vcn_id              = oci_core_vcn.this.id
  display_name        = "iicpc-${var.environment}-data"
  cidr_block          = var.data_subnet_cidr
  dns_label           = "data"
  prohibit_public_ip_on_vnic = true
  route_table_id      = oci_core_route_table.private.id
  security_list_ids   = [oci_core_security_list.data.id]
  dhcp_options_id     = oci_core_vcn.this.default_dhcp_options_id
}

# Route tables
resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "iicpc-${var.environment}-public-rt"
  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.this.id
  }
}

resource "oci_core_route_table" "private" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "iicpc-${var.environment}-private-rt"
  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_nat_gateway.this.id
  }
}

# Security lists
resource "oci_core_security_list" "public" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "iicpc-${var.environment}-public-sl"

  egress_security_rules {
    destination      = "0.0.0.0/0"
    protocol         = "all"
  }

  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    description = "HTTP"
    tcp_options {
      min = 80
      max = 80
    }
  }

  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    description = "HTTPS"
    tcp_options {
      min = 443
      max = 443
    }
  }

  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    description = "Grafana"
    tcp_options {
      min = 3000
      max = 3000
    }
  }

  ingress_security_rules {
    protocol    = "6"
    source      = var.vcn_cidr
    description = "Allow all TCP from VCN"
    tcp_options {
      min = 1
      max = 65535
    }
  }
}

resource "oci_core_security_list" "private" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "iicpc-${var.environment}-private-sl"

  egress_security_rules {
    destination      = "0.0.0.0/0"
    protocol         = "all"
  }

  ingress_security_rules {
    protocol    = "6"
    source      = var.vcn_cidr
    description = "Allow all TCP from VCN"
    tcp_options {
      min = 1
      max = 65535
    }
  }
}

resource "oci_core_security_list" "data" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "iicpc-${var.environment}-data-sl"

  egress_security_rules {
    destination      = "0.0.0.0/0"
    protocol         = "all"
  }

  ingress_security_rules {
    protocol    = "6"
    source      = var.private_subnet_cidr
    description = "PostgreSQL"
    tcp_options {
      min = 5432
      max = 5432
    }
  }

  ingress_security_rules {
    protocol    = "6"
    source      = var.private_subnet_cidr
    description = "Redis"
    tcp_options {
      min = 6379
      max = 6379
    }
  }

  ingress_security_rules {
    protocol    = "6"
    source      = var.private_subnet_cidr
    description = "Kafka"
    tcp_options {
      min = 9092
      max = 9092
    }
  }

  ingress_security_rules {
    protocol    = "6"
    source      = var.private_subnet_cidr
    description = "gRPC"
    tcp_options {
      min = 50051
      max = 50053
    }
  }
}
