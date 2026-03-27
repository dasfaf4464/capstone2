@echo off
cd /d "%~dp0"
cd ..

echo --------------------------------------------------
echo 경고: 모든 데이터베이스와 미디어 파일을 삭제합니다.
echo 프로젝트를 완전히 초기 상태로 되돌립니다.
echo 현재 위치: %cd% (프로젝트 루트에서 스크립트 실행중)
echo --------------------------------------------------

echo [1/4] 기존 컨테이너 및 볼륨 제거 중...
docker-compose down -v

echo [2/4] 임시 미디어 폴더(uploads, results) 삭제 중...
rmdir /s /q media_storage\uploads
rmdir /s /q media_storage\results
mkdir media_storage\uploads
mkdir media_storage\results

echo [3/4] DB 데이터 및 로그 폴더 삭제 중...
rmdir /s /q postgresql\db_data
rmdir /s /q neo4j\data
rmdir /s /q neo4j\logs
mkdir postgresql\db_data
mkdir neo4j\data
mkdir neo4j\logs

echo [4/4] 완전히 비워진 상태로 다시 빌드 중...
docker-compose up -d --build

echo 완료! 모든 데이터가 초기화되었습니다.
pause