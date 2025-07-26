@echo off
echo ============================================
echo 보이스피싱 탐지 시스템 웹 API 테스트 실행
echo ============================================
echo.

cd /d "%~dp0\.."

echo Django 서버 연결 확인...
curl -s "http://127.0.0.1:8000/" > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Django 서버에 연결할 수 없습니다.
    echo 먼저 Django 서버를 실행해주세요:
    echo   cd ..
    echo   uv run python manage.py runserver
    echo.
    pause
    exit /b 1
)
echo [OK] Django 서버 연결 확인됨
echo.

echo [1/3] 실제 음성 파일 테스트...
uv run python utils/test_real_voice_file.py
if errorlevel 1 (
    echo [ERROR] 실제 음성 파일 테스트 실패
    pause
    exit /b 1
)
echo.

echo [2/3] 엔드투엔드 워크플로우 테스트...
uv run python utils/test_end_to_end.py
if errorlevel 1 (
    echo [ERROR] 엔드투엔드 테스트 실패
    pause
    exit /b 1
)
echo.

echo [3/3] 최종 종합 테스트...
uv run python utils/final_comprehensive_test.py
if errorlevel 1 (
    echo [ERROR] 최종 종합 테스트 실패
    pause
    exit /b 1
)
echo.

echo ============================================
echo 모든 웹 API 테스트가 완료되었습니다!
echo ============================================
pause