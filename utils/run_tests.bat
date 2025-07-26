@echo off
echo ============================================
echo 보이스피싱 탐지 시스템 유틸리티 테스트 실행
echo ============================================
echo.

cd /d "%~dp0\.."

echo [1/4] 데이터베이스 스키마 확인...
uv run python utils/check_db_schema.py
if errorlevel 1 (
    echo [ERROR] 데이터베이스 스키마 확인 실패
    pause
    exit /b 1
)
echo.

echo [2/4] 데이터베이스 연동 테스트...
uv run python utils/test_db_integration.py
if errorlevel 1 (
    echo [ERROR] 데이터베이스 연동 테스트 실패
    pause
    exit /b 1
)
echo.

echo [3/4] 피드백 데이터 확인...
uv run python utils/check_feedback_data.py
echo.

echo [4/4] 피드백 디버깅 테스트...
uv run python utils/debug_feedback.py
echo.

echo ============================================
echo 모든 로컬 테스트가 완료되었습니다!
echo ============================================
echo.
echo 웹 API 테스트를 위해서는 Django 서버를 먼저 실행하세요:
echo   cd ..
echo   uv run python manage.py runserver
echo.
echo 그 후 다음 스크립트들을 실행할 수 있습니다:
echo   - test_real_voice_file.py
echo   - test_end_to_end.py  
echo   - final_comprehensive_test.py
echo.
pause