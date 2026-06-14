output "cluster_id" {
  value = oci_containerengine_cluster.this.id
}

output "cluster_name" {
  value = oci_containerengine_cluster.this.name
}

output "node_pool_id" {
  value = oci_containerengine_node_pool.this.id
}

output "kubeconfig" {
  value = oci_containerengine_cluster.this.kubeconfig
}

data "oci_containerengine_cluster_kube_config" "this" {
  cluster_id = oci_containerengine_cluster.this.id
}
