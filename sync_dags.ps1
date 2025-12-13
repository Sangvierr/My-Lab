# 1. Encoding Setup
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ">>> Starting Airflow DAG deployment..." -ForegroundColor Green

# 2. Check dags folder
if (-not (Test-Path "dags")) {
    Write-Error "[e] Error: 'dags' folder not found. Please run this script from the project root (MY-LAB)."
    exit 1
}

# 3. Get Airflow Pods
$podsOutput = kubectl get pods -n airflow --no-headers -o custom-columns=":metadata.name"

# Check if pods exist
if (-not $podsOutput) {
    Write-Error "[e] Error: No Airflow pods found. Check if Docker/Kubernetes is running."
    exit 1
}

# Split by newline
$podList = $podsOutput -split "\r?\n"

# 4. Deploy (Copy files)
foreach ($pod in $podList) {
    # Skip empty lines
    if ([string]::IsNullOrWhiteSpace($pod)) { continue }

    # Filter target pods: scheduler, dag-processor, worker, api-server
    if ($pod -match "scheduler|dag-processor|worker|api-server") {
        Write-Host "[i] Deploying to: $pod" -ForegroundColor Cyan
        
        kubectl cp dags "airflow/$($pod):/opt/airflow/" 2>$null
    }
}

Write-Host ">>> Deployment completed! Please refresh the Airflow UI." -ForegroundColor Green