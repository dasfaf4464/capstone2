#!/bin/bash
cd "$(dirname "$0")/.."

echo "--------------------------------------------------"
echo "경고: 모든 데이터베이스와 미디어 파일을 삭제합니다."
echo "프로젝트를 완전히 초기 상태로 되돌립니다."
echo "현재 위치: $(pwd) (프로젝트 루트에서 스크립트 실행중)"
echo "--------------------------------------------------"

echo "[1/4] 기존 컨테이너 및 볼륨 제거 중..."
docker-compose down -v

echo "[2/4] 임시 미디어 폴더(uploads, results) 비우는 중..."
rm -rf media_storage/uploads/* media_storage/results/*

echo "[3/4] DB 데이터 및 로그 폴더 비우는 중..."
rm -rf postgresql/db_data/* neo4j/data/* neo4j/logs/*

echo "[4/4] 완전히 비워진 상태로 다시 빌드 중..."
docker-compose up -d --build

echo "완료! 모든 데이터가 초기화되었습니다."
read -n 1 -s -r -p "계속하려면 아무 키나 누르세요..."
echo ""