<#
.SYNOPSIS
    Kind Cluster Management Script for IICPC Platform (PowerShell)

.DESCRIPTION
    Manages a local Kind Kubernetes cluster for IICPC Platform development.

.EXAMPLE
    .\scripts\kind-cluster.ps1 create
    .\scripts\kind-cluster.ps1 load-images
    .\scripts\kind-cluster.ps1 status
#>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet('create', 'delete', 'load-images', 'status', 'logs')]
    [string]$Command
)

$ClusterName = "iicpc"
$KindConfig = "kind-config.yaml"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir

function Write-LogInfo { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-LogSuccess { param($msg) Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Write-LogWarn { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-LogError { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

function Check-Dependencies {
    $missing = @()
    foreach ($cmd in 'kind', 'docker', 'kubectl') {
        if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
            $missing += $cmd
        }
    }
    if ($missing.Count -gt 0) {
        Write-LogError "Missing dependencies: $($missing -join ', ')"
        Write-LogInfo "Install: kind (https://kind.sigs.k8s.io), docker, kubectl"
        exit 1
    }
}

function Create-Cluster {
    Write-LogInfo "Creating Kind cluster '$ClusterName'..."
    if (kind get clusters | Where-Object { $_ -eq $ClusterName }) {
        Write-LogWarn "Cluster '$ClusterName' already exists"
        return
    }
    
    Set-Location $ProjectRoot
    kind create cluster --name $ClusterName --config $KindConfig
    
    Write-LogInfo "Waiting for nodes to be ready..."
    kubectl wait --for=condition=Ready nodes --all --timeout=120s
    
    Write-LogSuccess "Cluster '$ClusterName' created successfully"
    Write-LogInfo "Cluster nodes:"
    kubectl get nodes -o wide
}

function Delete-Cluster {
    Write-LogInfo "Deleting Kind cluster '$ClusterName'..."
    kind delete cluster --name $ClusterName
    Write-LogSuccess "Cluster '$ClusterName' deleted"
}

function Load-Images {
    Write-LogInfo "Loading Docker images into Kind cluster..."
    
    $images = @(
        "iicpc-hosting:latest"
        "iicpc-botfleet:latest"
        "iicpc-evaluation:latest"
        "iicpc-federation:latest"
        "iicpc-governance:latest"
        "iicpc-strategic:latest"
        "iicpc-dashboard:latest"
    )
    
    foreach ($img in $images) {
        Write-LogInfo "Loading $img..."
        try {
            kind load docker-image $img --name $ClusterName
        } catch {
            Write-LogWarn "Failed to load $img (image may not exist locally)"
        }
    }
    
    Write-LogSuccess "Images loaded"
}

function Show-Status {
    Write-LogInfo "Cluster: $ClusterName"
    if (kind get clusters | Where-Object { $_ -eq $ClusterName }) {
        Write-LogSuccess "Cluster exists"
        Write-Host ""
        Write-LogInfo "Nodes:"
        kubectl get nodes -o wide
        Write-Host ""
        Write-LogInfo "Pods (all namespaces):"
        kubectl get pods -A -o wide
        Write-Host ""
        Write-LogInfo "Services:"
        kubectl get svc -A
    } else {
        Write-LogWarn "Cluster does not exist"
    }
}

function Show-Logs {
    Write-LogInfo "Showing control plane logs..."
    $logPath = "$env:TEMP\kind-logs"
    kind export logs --name $ClusterName $logPath 2>$null
    if (Test-Path $logPath) {
        Get-ChildItem $logPath | Format-Table Name, Length, LastWriteTime
    }
}

switch ($Command) {
    'create' { Check-Dependencies; Create-Cluster }
    'delete' { Check-Dependencies; Delete-Cluster }
    'load-images' { Check-Dependencies; Load-Images }
    'status' { Check-Dependencies; Show-Status }
    'logs' { Check-Dependencies; Show-Logs }
}