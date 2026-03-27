#!/bin/bash
cd "$(dirname "$0")/.."

echo "--------------------------------------------------"
echo "기존 컨테이너를 내리고 임시 미디어 파일을 삭제합니다."
echo "데이터 베이스는 유지됩니다."
echo "현재 위치: $(pwd) (프로젝트 루트에서 스크립트 실행중)"
echo "--------------------------------------------------"

echo "[1/3] 기존 컨테이너 내리는 중..."
docker-compose down

echo "[2/3] 임시 미디어 폴더(uploads, results) 비우는 중..."
rm -rf media_storage/uploads/* media_storage/results/*

echo "[3/3] 다시 빌드 및 백그라운드 실행 중..."
docker-compose up -d --build

echo "완료! 미디어 폴더가 초기화되었습니다."
read -n 1 -s -r -p "계속하려면 아무 키나 누르세요..."
echo ""