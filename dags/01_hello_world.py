from airflow import DAG
from airflow.decorators import task
from datetime import datetime, timedelta

# 1. DAG(작업 흐름) 정의
with DAG(
    dag_id="01_hello_mylab",            # Airflow 화면에 뜰 이름
    start_date=datetime(2025, 1, 1),    # 시작일 
    schedule=None,                      # 수동 트리거
    catchup=False,                      # 밀린 작업 안 함
    tags=["mylab", "test"],             # 태그
) as dag:

    # 2. 작업(Task) 정의
    @task
    def print_hello():
        print("-" * 30)
        print("🚀 Hello! This code was written on Mac, running on Windows GPU!")
        print("-" * 30)

    # 3. 작업 실행
    print_hello()