# Utils 폴더

이 폴더에는 보이스피싱 탐지 시스템의 디버깅, 테스트, 검증을 위한 유틸리티 스크립트들이 포함되어 있습니다.

## 파일 목록

### 데이터베이스 관련
- **`check_db_schema.py`**: 데이터베이스 스키마 확인 및 마이그레이션 상태 검증
- **`check_feedback_data.py`**: 피드백 데이터 확인 및 검색 테스트

### 디버깅 도구
- **`debug_feedback.py`**: 피드백 제출 기능 디버깅
- **`debug_frontend_feedback.py`**: 프론트엔드 피드백 제출 문제 디버깅

### 테스트 스크립트
- **`test_db_integration.py`**: 데이터베이스 연동 테스트
- **`test_end_to_end.py`**: 전체 엔드투엔드 워크플로우 테스트
- **`test_real_voice_file.py`**: 실제 보이스피싱 음성 파일로 시스템 테스트
- **`final_comprehensive_test.py`**: 최종 종합 테스트

### 유틸리티
- **`update_all_django_paths.py`**: Django 경로 설정 일괄 수정 도구

## 사용법

### 기본 실행
모든 스크립트는 utils 폴더에서 실행해야 합니다:

```bash
cd utils
python 스크립트명.py
```

### 권장 실행 순서

1. **시스템 설정 확인**
   ```bash
   python check_db_schema.py
   ```

2. **데이터베이스 연동 테스트**
   ```bash
   python test_db_integration.py
   ```

3. **실제 파일로 테스트** (서버 실행 필요)
   ```bash
   # 먼저 Django 서버를 실행하세요:
   cd ..
   uv run python manage.py runserver
   
   # 새 터미널에서:
   cd utils
   python test_real_voice_file.py
   ```

4. **전체 엔드투엔드 테스트** (서버 실행 필요)
   ```bash
   python test_end_to_end.py
   ```

5. **최종 종합 테스트** (서버 실행 필요)
   ```bash
   python final_comprehensive_test.py
   ```

### 디버깅이 필요한 경우

- **피드백 문제 진단**: `python debug_feedback.py`
- **프론트엔드 연동 문제**: `python debug_frontend_feedback.py`
- **데이터 확인**: `python check_feedback_data.py`

## 주의사항

1. **Django 서버 상태**: 웹 API 테스트 스크립트들은 Django 서버가 실행 중이어야 합니다.
2. **데이터베이스 연결**: 모든 스크립트는 Django 설정을 사용하므로 데이터베이스가 올바르게 설정되어 있어야 합니다.
3. **파일 경로**: 실제 음성 파일 테스트는 지정된 경로에 테스트 파일이 있어야 합니다.

## 문제 해결

- **import 오류**: Django 설정 경로 문제일 수 있습니다. `update_all_django_paths.py`를 실행해보세요.
- **연결 오류**: Django 서버가 실행 중인지 확인하세요.
- **권한 오류**: Windows에서는 관리자 권한이 필요할 수 있습니다.