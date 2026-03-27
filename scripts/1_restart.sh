#!/bin/bash

# 스크립트 위치로 이동 후 한 단계 위(루트)로 이동
cd "$(dirname "$0")/.."

echo "--------------------------------------------------"
echo "기존 컨테이너를 내리고 다시 빌드합니다."
echo "기존 미디어 폴더, 데이터 베이스는 유지됩니다."
echo "현재 위치: $(pwd) (프로젝트 루트에서 스크립트 실행중)"
echo "--------------------------------------------------"

echo ""
echo "[1/2] 기존 컨테이너 내리는 중..."
docker-compose down

echo ""
echo "[2/2] 다시 빌드 및 백그라운드 실행 중..."
docker-compose up -d --build

echo ""
echo "완료! localhost:5000 (Flask) / localhost:7474 (Neo4j) 확인!"

# 윈도우의 pause와 같은 기능 (키 입력 대기)
read -n 1 -s -r -p "계속하려면 아무 키나 누르세요..."
echo ""