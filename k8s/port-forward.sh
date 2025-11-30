#!/bin/bash
echo "🔌 Connecting to Airflow UI..."
echo "👉 http://localhost:8080 (admin/admin)"
echo "---------------------------------------"
kubectl port-forward svc/airflow-api-server 8080:8080 -n airflow