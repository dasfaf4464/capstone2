@echo off
cd /d "%~dp0"
cd ..

echo --------------------------------------------------
echo ���: ��� �����ͺ��̽��� �̵�� ������ �����մϴ�.
echo ������Ʈ�� ������ �ʱ� ���·� �ǵ����ϴ�.
echo ���� ��ġ: %cd% (������Ʈ ��Ʈ���� ��ũ��Ʈ ������)
echo --------------------------------------------------

echo [1/4] ���� �����̳� �� ���� ���� ��...
docker-compose down -v

echo [2/4] �ӽ� �̵�� ����(uploads, results) ���� ��...
rmdir /s /q media_storage\uploads
rmdir /s /q media_storage\results
mkdir media_storage\uploads
mkdir media_storage\results

echo [3/4] DB ������ �� �α� ���� ���� ��...
rmdir /s /q postgresql\db_data
mkdir postgresql\db_data

echo [4/4] ������ ����� ���·� �ٽ� ���� ��...
docker-compose up -d --build

echo �Ϸ�! ��� �����Ͱ� �ʱ�ȭ�Ǿ����ϴ�.
pause