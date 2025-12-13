#!/bin/bash

# 색상 코드
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "🚀 Airflow DAG 배포를 시작합니다..."

# 1. dags 폴더가 있는지 확인
if [ ! -d "dags" ]; then
    echo "❌ 에러: 'dags' 폴더가 안 보입니다. 프로젝트 루트(MY-LAB)에서 실행해주세요."
    exit 1
fi

# 2. Airflow 파드 목록 가져오기
PODS=$(kubectl get pods -n airflow -o jsonpath='{range .items[*]}{.metadata.name}{" "}{end}')

# 3. 관련된 파드들에 dags 폴더 통째로 복사
for pod in $PODS; do
    # 스케줄러, 프로세서, 워커, API서버만 골라냄
    if [[ $pod == *"scheduler"* ]] || [[ $pod == *"dag-processor"* ]] || [[ $pod == *"worker"* ]] || [[ $pod == *"api-server"* ]]; then
        echo -e "📦 배송 중: ${GREEN}$pod${NC}"
        
        # dags 폴더를 파드 내부의 /opt/airflow 경로로 복사 (덮어쓰기)
        kubectl cp dags airflow/$pod:/opt/airflow/
    fi
done

echo "✅ 모든 배포가 완료되었습니다! Airflow 화면을 새로고침 하세요."
