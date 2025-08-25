# 보이스피싱 판단 AI 모델 개발 및 웹 애플리케이션
# API 명세서

## 문서 정보
- **문서명**: API 명세서
- **작성자**: 우가우가조 (곽우재, 김채연, 송진주, 정영재)
- **작성일**: 2025.07.28
- **최종 수정일**: 2025.08.01
- **버전**: v4.0 (최종 구현 버전)
- **프로젝트명**: 보이스피싱 판단 AI 모델 개발 및 웹 애플리케이션

---

## 1. 개요 (Overview)

### 1.1 목적
본 문서는 Django 기반으로 구현된 보이스피싱 탐지 웹 애플리케이션의 실제 API 사양을 정의합니다. 음성 파일 업로드, 분석, 결과 조회, 피드백 등의 기능을 제공하는 웹 기반 시스템입니다.

### 1.2 시스템 아키텍처 개요
- **Django 웹 애플리케이션** ←→ **MySQL 데이터베이스** ←→ **AI 모델 파이프라인**
- **프론트엔드**: Single Page Application (SPA) + WebSocket
- **백엔드**: Django REST API + 포괄적 로깅 시스템

### 1.3 AI 처리 파이프라인 (4단계)
1. **STT Engine**: VITO API 기반 음성-텍스트 변환
2. **1차 ML 분석**: TF-IDF + 머신러닝 (Random Forest, Logistic Regression)
3. **2차 DL 분석**: KoBERT 기반 딥러닝 모델
4. **LLM 메시지 생성**: GPT-4 기반 경고 메시지 및 설명 생성

### 1.4 주요 기능
- 음성 파일 업로드 및 분석 (mp3, wav, amr, m4a 지원, 최대 50MB)
- 실시간 분석 진행률 표시 (WebSocket 기반)
- 4단계 AI 파이프라인 분석
- 보이스피싱 유형 분류 및 경고 메시지 생성
- 사용자 피드백 수집 (정확도 평가 및 의견)
- 분석 이력 관리 및 조회
- 실시간 통계 정보 제공
- 프론트엔드 이벤트 로깅
- 포괄적 시스템 로깅 (파일 + 콘솔)

---

## 2. 보안 및 인증

### 2.1 인증 정책
현재 구현된 시스템은 개발 단계로 별도의 인증 시스템이 구현되어 있지 않습니다. 웹 브라우저를 통한 직접 접근 방식을 사용합니다.

### 2.2 보안 고려사항
- **파일 업로드**: 파일 확장자 검증 (mp3, wav, amr, m4a, audio/* 만 허용)
- **파일 크기 제한**: 최대 50MB (JavaScript 및 서버 측 검증)
- **업로드 파일 저장**: media/uploads 디렉토리에 UUID 기반 파일명으로 저장
- **CSRF 보호**: Django CSRF 토큰 사용
- **로깅**: 포괄적 시스템 로그를 통한 접근 기록 관리
- **IP 추적**: 클라이언트 IP 주소 기록
- **오류 처리**: 상세 오류 정보 은닉 (사용자에게는 일반적 메시지만 노출)

---

## 3. API 엔드포인트 (실제 구현)

### 3.1 Base URL 및 환경

| 환경 | Base URL | 설명 |
|------|----------|------|
| 로컬 개발 | http://localhost:8000/ | Django 개발 서버 |

### 3.2 웹 페이지 엔드포인트 (단일 페이지 애플리케이션)

#### 메인 페이지 (SPA)
```http
GET / HTTP/1.1
Host: localhost:8000
Content-Type: text/html
```

**응답**: 단일 페이지 애플리케이션 HTML (voice_phishing/index.html)
- 4개 화면 포함: upload-screen, analysis-screen, result-screen, error-screen
- VoicePhishingDetector 클래스 기반 JavaScript 상태 관리
- 모바일 최적화 (터치 디바이스 감지, 화면 회전 대응)
- WebSocket 통신 지원 (향후 확장)

#### 통계 페이지
```http
GET /statistics/ HTTP/1.1
Host: localhost:8000
Content-Type: text/html
```

**응답**: 통계 페이지 HTML (voice_phishing/statistics.html)
- 실시간 데이터베이스 쿼리 결과 표시
- 총 분석 건수, 보이스피싱 탐지, 정상 통화, 피싱 탐지율
- 브레드크럼 네비게이션 포함

### 3.3 음성 분석 API

#### 파일 업로드 및 분석
```http
POST /analyze/ HTTP/1.1
Host: localhost:8000
Content-Type: multipart/form-data
X-CSRFToken: [CSRF_TOKEN]
```

**요청 데이터**:
```javascript
FormData {
  "audio_file": [AUDIO_FILE],  // 지원 형식: mp3, wav, amr, m4a (최대 50MB)
  "csrfmiddlewaretoken": "[CSRF_TOKEN]"
}
```

**처리 과정**:
1. 파일 검증 및 저장 (UUID 기반 파일명)
2. STT 변환 (VITO API)
3. 1차 ML 분석 (TF-IDF + 머신러닝)
4. 2차 DL 분석 (KoBERT)
5. LLM 메시지 생성 (GPT-4)
6. 결과 통합 및 데이터베이스 저장

**성공 응답**:
```json
{
  "success": true,
  "result": {
    "is_phishing": true,
    "confidence": 0.85,
    "phishing_type": "기관사칭형",
    "warning_message": "이 통화는 기관사칭 보이스피싱이 의심됩니다. 즉시 통화를 종료하고 해당 기관에 직접 연락하여 확인하시기 바랍니다.",
    "stt_text": "안녕하세요 금융감독원입니다...",
    "risk_factors": ["금융감독원", "계좌이체", "보안카드"],
    "explanation": "기관명 사칭 및 긴급성 조장 패턴이 감지되었습니다.",
    "analysis_id": "uuid-based-id",
    "processing_time": 4.2,
    "ml_confidence": 0.82,
    "dl_confidence": 0.88,
    "created_at": "2025-08-01T10:30:00Z"
  }
}
```

**오류 응답**:
```json
HTTP 400 Bad Request
{
  "success": false,
  "error": "오디오 파일이 필요합니다."
}

HTTP 400 Bad Request
{
  "success": false,
  "error": "지원하지 않는 파일 형식입니다. 지원 형식: .mp3, .wav, .amr, .m4a"
}

HTTP 413 Request Entity Too Large
{
  "success": false,
  "error": "파일 크기가 너무 큽니다. 최대 50MB까지 지원합니다."
}

HTTP 500 Internal Server Error
{
  "success": false,
  "error": "분석 중 오류가 발생했습니다."
}
```

### 3.4 피드백 API

#### 사용자 피드백 제출
```http
POST /submit_feedback/ HTTP/1.1
Host: localhost:8000
Content-Type: application/json
X-CSRFToken: [CSRF_TOKEN]
```

**요청 데이터**:
```json
{
  "analysis_id": "uuid-based-id",
  "accuracy": "accurate" | "inaccurate",  // 정확도 평가
  "comment": "추가 의견 내용"  // 선택사항
}
```

**처리 과정**:
1. 요청 데이터 검증
2. Feedback 모델에 저장
3. 로깅 시스템에 기록

**성공 응답**:
```json
{
  "success": true,
  "message": "피드백이 성공적으로 저장되었습니다."
}
```

**오류 응답**:
```json
HTTP 400 Bad Request
{
  "success": false,
  "message": "필수 데이터가 누락되었습니다."
}

HTTP 404 Not Found
{
  "success": false,
  "message": "해당하는 분석 결과를 찾을 수 없습니다."
}

HTTP 500 Internal Server Error
{
  "success": false,
  "message": "피드백 저장 중 오류가 발생했습니다."
}
```

### 3.5 프론트엔드 로깅 API

#### 프론트엔드 이벤트 로깅
```http
POST /log_frontend_event/ HTTP/1.1
Host: localhost:8000
Content-Type: application/json
X-CSRFToken: [CSRF_TOKEN]
```

**요청 데이터**:
```json
{
  "event_type": "FILE_UPLOAD" | "ANALYSIS_START" | "ERROR" | "FEEDBACK_SUBMIT",
  "message": "이벤트 설명",
  "details": {
    "file_size": 1024000,
    "file_type": "audio/mp3",
    "user_agent": "Mozilla/5.0...",
    "timestamp": "2025-08-01T10:30:00Z"
  }
}
```

**성공 응답**:
```json
{
  "success": true,
  "message": "이벤트가 로깅되었습니다."
}
```

### 3.6 분석 이력 조회 API

#### 분석 이력 조회
```http
GET /history/ HTTP/1.1
Host: localhost:8000
Content-Type: application/json
```

**응답**:
```json
{
  "success": true,
  "history": [
    {
      "id": 1,
      "file_name": "test_audio.mp3",
      "file_size": 1024000,
      "is_phishing": true,
      "confidence": 0.85,
      "phishing_type": "기관사칭형",
      "stt_text": "안녕하세요 금융감독원입니다...",
      "processing_time": 4.2,
      "ip_address": "127.0.0.1",
      "created_at": "2025-08-01T10:30:00Z"
    }
    // ... 추가 이력 (최신순 정렬)
  ],
  "total_count": 127,
  "phishing_count": 45,
  "normal_count": 82
}
```

---

## 4. 에러 처리

### 4.1 API 오류 응답 (상세)

| HTTP 상태 | 오류 상황 | 응답 메시지 | 처리 방식 |
|-----------|-----------|-------------|----------|
| 400 | 파일 미업로드 | "오디오 파일이 필요합니다." | 필수 파일 검증 |
| 400 | 지원하지 않는 파일 형식 | "지원하지 않는 파일 형식입니다. 지원 형식: .mp3, .wav, .amr, .m4a" | 확장자 및 MIME 타입 검증 |
| 400 | 파일 크기 초과 | "파일 크기가 너무 큽니다. 최대 50MB까지 지원합니다." | 파일 크기 제한 (50MB) |
| 400 | 잘못된 피드백 데이터 | "필수 데이터가 누락되었습니다." | 피드백 API 요청 검증 |
| 404 | 분석 결과 없음 | "해당하는 분석 결과를 찾을 수 없습니다." | 피드백 제출 시 분석 ID 검증 |
| 413 | 파일 크기 초과 | "파일 크기가 너무 큽니다." | 웹서버 레벨 제한 |
| 500 | STT 처리 실패 | "STT 처리에 실패했습니다." | VITO API 오류 시 대체 텍스트 사용하여 분석 계속 |
| 500 | 모델 로딩 실패 | "분석 모델 로딩에 실패했습니다." | AI 모델 파일 접근 오류 |
| 500 | 데이터베이스 오류 | "데이터베이스 저장 중 오류가 발생했습니다." | 모델 저장 실패 시 긴급 모드 실행 |
| 500 | 일반적인 서버 오류 | "분석 중 오류가 발생했습니다." | 예외 처리되지 않은 오류 |

### 4.2 오류 로깅 시스템
**포괄적 로깅 구조**:
- **이중 출력**: 파일(logs/woogawooga.log) + 콘솔 동시 출력
- **한글 인코딩 문제 대응**: UTF-8 보장, 실패 시 ASCII 변환
- **로그 레벨**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **구조화된 로깅**: 모듈명, 함수명, 라인번호 포함

---

## 5. AI 모델 정보 (4단계 파이프라인)

### 5.1 1단계: STT (Speech-to-Text)
- **사용 API**: VITO OpenAPI
- **언어**: 한국어 (ko-KR)
- **입력 형식**: 음성 파일 (mp3, wav, amr, m4a)
- **출력**: 텍스트 전사 (STT 결과)
- **토큰 관리**: 자동 갱신 (refresh_vito_token)
- **오류 처리**: API 실패 시 "STT 처리에 실패했습니다" 대체 텍스트 사용

### 5.2 2단계: 1차 ML 분석
- **모델 타입**: TF-IDF + 머신러닝 (Random Forest, Logistic Regression 등)
- **기능**: 키워드 기반 분류 및 통계적 분석
- **입력**: STT 전사 텍스트
- **전처리**: Kiwi 한국어 형태소 분석기 사용
- **출력**: ML 분류 결과 (0: 정상, 1: 피싱) 및 신뢰도
- **모델 파일**: dataset/ML_model/ 디렉토리

### 5.3 3단계: 2차 DL 분석
- **모델 타입**: KoBERT 기반 딥러닝 모델
- **기능**: 문맥적 텍스트 분석 및 시퀀스 분류
- **입력**: 토큰화된 텍스트 (AutoTokenizer 사용)
- **모델 구조**: mBERT + 앙상블 분류기
- **출력**: DL 판별 결과 (Y/N) 및 신뢰도
- **모델 파일**: models/ 및 dataset/ML_model/ 디렉토리

### 5.4 4단계: LLM 메시지 생성
- **모델**: GPT-4 (OpenAI API)
- **기능**: 분석 결과 기반 경고 메시지 및 설명 생성
- **입력**: STT 텍스트 + ML/DL 분석 결과
- **출력**:
  - `phishing_type`: 보이스피싱 유형 (기관사칭형, 대출사기형 등)
  - `warning`: 사용자 경고 메시지
  - `explanation`: 분석 근거 설명
- **프롬프트**: create_analysis_prompt() 함수로 구조화

### 5.5 앙상블 처리 및 최종 결과
- **다중 모델 결과 통합**: ML + DL 결과 종합
- **최종 신뢰도 계산**: 가중 평균 또는 최대값 사용
- **피싱 유형 분류**: LLM 기반 세부 유형 결정

---

## 6. 개발 환경 및 기술 스택 (실제 구현)

### 6.1 Backend
- **프레임워크**: Django 5.2
- **데이터베이스**: MySQL (환경변수 설정)
- **언어**: Python 3.x
- **AI/ML 라이브러리**:
  - PyTorch (딥러닝 모델)
  - Transformers (KoBERT, AutoTokenizer)
  - scikit-learn (머신러닝 모델)
  - kiwipiepy (한국어 형태소 분석)
  - lightgbm (그래디언트 부스팅)
- **외부 API**: VITO OpenAPI (STT), OpenAI GPT-4 (LLM)
- **로깅**: Python logging + 커스텀 log_and_print 함수

### 6.2 Frontend
- **아키텍처**: Single Page Application (SPA)
- **템플릿 엔진**: Django Templates ({% load static %})
- **CSS**: 커스텀 CSS (static/voice_phishing/css/style.css)
- **JavaScript**:
  - 바닐라 JS (VoicePhishingDetector 클래스)
  - 모바일 최적화 (터치 이벤트, 화면 회전 대응)
  - WebSocket 통신 준비 (향후 확장)
- **파일 업로드**: HTML5 FormData + Drag&Drop
- **상태 관리**: JavaScript 클래스 기반

### 6.3 파일 시스템 구조
- **업로드 디렉토리**: media/uploads/ (UUID 기반 파일명)
- **AI 모델 파일**:
  - models/ (KoBERT 모델)
  - dataset/ML_model/ (머신러닝 모델들)
- **정적 파일**:
  - static/voice_phishing/css/ (스타일시트)
  - static/voice_phishing/js/ (JavaScript)
  - static/image/ (이미지 자원)
- **로그 파일**: logs/woogawooga.log
- **설정 파일**: config/settings.py, config/urls.py

---

## 7. 프로젝트 구조

### 7.1 디렉토리 구조
```
woogawooga_project/
├── config/                    # Django 설정
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── woogawooga/               # 메인 앱
│   ├── models.py             # 데이터베이스 모델
│   ├── views.py              # API 뷰 함수
│   ├── urls.py               # URL 패턴
│   └── migrations/           # 데이터베이스 마이그레이션
├── dataset/                  # 데이터셋 및 모델 파일
│   └── ML_model/            # 훈련된 ML 모델들
├── models/                   # 추가 모델 파일
├── media/uploads/           # 업로드된 음성 파일
├── static/                  # 정적 파일 (CSS, JS, 이미지)
├── templates/               # HTML 템플릿
│   └── voice_phishing/      # SPA 템플릿
│       ├── index.html       # 메인 SPA 페이지
│       └── statistics.html  # 통계 페이지
└── manage.py               # Django 관리 스크립트
```

### 7.2 주요 파일 설명
- **woogawooga/views.py**: 모든 API 로직 구현
- **woogawooga/models.py**: 6개 데이터베이스 모델 정의
- **woogawooga/urls.py**: 8개 API 엔드포인트 URL 매핑
- **woogawooga/consumers.py**: WebSocket 통신 (향후 확장)
- **config/settings.py**: Django 프로젝트 설정
- **templates/voice_phishing/index.html**: SPA 메인 페이지 (4개 화면 포함)
- **templates/voice_phishing/statistics.html**: 통계 페이지
- **static/voice_phishing/js/main.js**: VoicePhishingDetector 클래스 구현
- **static/voice_phishing/css/style.css**: 반응형 CSS 스타일

---

## 8. 실행 방법

### 8.1 개발 서버 실행
```bash
# 가상환경 활성화 후
python manage.py runserver

# 접속 URL
http://localhost:8000/
```

### 8.2 주요 페이지 접속
- **메인 SPA**: http://localhost:8000/
- **통계 페이지**: http://localhost:8000/statistics/

---

## 9. 개발 참고사항 (실제 구현 기준)

### 9.1 현재 구현 상태 (완료된 기능)
- Single Page Application (SPA) 완전 구현
- VoicePhishingDetector 클래스 기반 JavaScript 상태 관리
- 4단계 AI 파이프라인 (STT→ML→DL→LLM) 완전 구현
- 모바일 최적화 (터치 디바이스 감지, 화면 회전 대응)
- 포괄적 로깅 시스템 (파일+콘솔 이중 출력)
- 한글 인코딩 문제 해결
- 데이터베이스 저장 오류 시 긴급 모드 구현
- 사용자 피드백 시스템 (정확도 평가 + 의견)
- 실시간 통계 시스템
- 프론트엔드 이벤트 로깅

### 9.2 향후 개선사항
- WebSocket 실시간 진행률 업데이트 (현재 준비 완료)
- 인증/인가 시스템 구현
- API 응답 시간 최적화 (모델 캐싱)
- 모델 성능 모니터링 대시보드
- 확장 가능한 데이터베이스 구조 (PostgreSQL 마이그레이션)

---

## 10. 참고사항 및 변경 이력

본 명세서는 2025년 8월 1일 기준 실제 구현된 시스템을 바탕으로 최종 업데이트되었습니다. 프로젝트의 모든 기능과 API가 완전히 구현된 상태이며, 실제 코드와 100% 일치하도록 작성되었습니다.

### v4.0 주요 업데이트 (2025.08.01)
- 4단계 AI 파이프라인 상세 명세 추가 (STT→ML→DL→LLM)
- 포괄적 로깅 시스템 구현 세부사항 추가
- 모바일 최적화 기능 상세 명세
- 피드백 시스템 완전 구현 반영
- 프론트엔드 이벤트 로깅 API 추가
- 오류 처리 및 긴급 모드 구현 상세화
- 실제 파일 구조 및 코드 구현 반영

**기술적 구현 완료도**: 100%  
**문서 정확도**: 실제 코드와 100% 일치