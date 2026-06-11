import os

dirs = [
    "iac/terraform/modules/networking",
    "iac/terraform/modules/kubernetes",
    "iac/terraform/modules/storage",
    "iac/terraform/modules/security",
    "iac/terraform/modules/monitoring",
    "iac/terraform/modules/backup",
    "iac/terraform/environments/dev",
    "iac/terraform/environments/staging",
    "iac/terraform/environments/production",
    "iac/kubernetes/manifests/dashboard",
    "iac/kubernetes/manifests/hosting",
    "iac/kubernetes/manifests/federation",
    "iac/kubernetes/manifests/evaluation",
    "iac/kubernetes/manifests/governance",
    "iac/kubernetes/manifests/strategic",
    "iac/kubernetes/manifests/botfleet",
    "iac/kubernetes/manifests/analytics",
    "iac/helm/iicpc-platform/templates",
    "iac/docker",
    "iac/gitops/argocd",
    "iac/gitops/flux",
    ".github/workflows",
    "dr",
    "gitops",
    "tests/iac",
    "tests/gitops"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    
files_to_touch = [
    "iac/helm/iicpc-platform/Chart.yaml",
    "iac/helm/iicpc-platform/values.yaml",
    "iac/docker/Dockerfile.dashboard",
    "iac/docker/Dockerfile.hosting",
    "iac/docker/Dockerfile.federation",
    "iac/docker/Dockerfile.evaluation",
    "iac/docker/Dockerfile.governance",
    "iac/docker/Dockerfile.strategic",
    "iac/docker/Dockerfile.botfleet",
    ".github/workflows/ci.yml",
    ".github/workflows/cd.yml",
    ".github/workflows/release.yml",
    ".github/workflows/security.yml"
]

for f in files_to_touch:
    open(f, 'w').close()
