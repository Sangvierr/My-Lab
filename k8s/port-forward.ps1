$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "[i] Connecting to Airflow UI (API Server)..." -ForegroundColor Cyan
Write-Host "[i] http://localhost:8888 (admin/admin)" -ForegroundColor Green
Write-Host "---------------------------------------"

# Airflow 3.0은 webserver 대신 api-server로 접속
kubectl port-forward svc/airflow-api-server 8888:8080 -n airflow