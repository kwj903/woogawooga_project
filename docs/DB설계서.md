# 보이스피싱 탐지 시스템 데이터베이스 설계서

## 문서 정보

| 항목 | 내용 |
|------|------|
| 문서명 | 데이터베이스 설계서 |
| 작성일자 | 2025.07.17 |
| 최종 수정일자 | 2025.08.25 |
| 버전 | v4.1 (보완 및 정규화 버전) |
| 작성자 | 우가우가팀 (곽우재, 김채연, 송진주, 정영재) |

## 1. 개요

본 설계서는 Django 기반 보이스피싱 탐지 시스템의 실제 구현된 데이터베이스 구조를 정의하고, 테이블 간의 관계, 속성, 제약조건 등을 상세히 문서화함으로써 개발 및 유지보수를 지원하는 것을 목적으로 한다.

### 1.1 시스템 개요

- **프레임워크**: Django 5.2
- **데이터베이스**: MySQL (운영용, 환경변수 설정), SQLite (개발용)
- **모델 총 개수**: 7개 (핵심 4개 + 시스템 2개 + 호환성 1개)
- **4단계 AI 파이프라인 지원**: STT → ML → DL → LLM
- **주요 기능**: 음성 파일 업로드, 실시간 STT 변환, 다층 AI 분석, 사용자 피드백, 통계 대시보드

## 2. 데이터베이스 아키텍처

### 2.1 테이블 구조 개요

본 시스템은 다음과 같은 주요 테이블로 구성됩니다:

#### 핵심 테이블 (4개)
- **ProcessdFile**: 업로드된 파일 및 STT 전사 결과 저장 (Primary)
- **InferenceResult**: AI 모델 추론 결과 저장 (Analysis Core)
- **ModelRegistry**: 사용 중인 AI 모델 등록 정보 (Configuration)
- **Feedback**: 사용자 피드백 정보 (User Interaction)

#### 시스템 테이블 (2개)
- **SystemLog**: 기존 호환성 시스템 로깅 (Legacy Logging)
- **VoicePhishingSystemLog**: 새로운 상세 시스템 로깅 (Enhanced Logging)

#### 호환성 테이블 (1개)
- **AnalysisResult**: UI 호환용 분석 결과 (Legacy UI Support)

## 3. 테이블 정의서 (실제 Django 모델 기준)

### 3.1 ProcessdFile - 처리된 파일 정보 테이블

- **Django 모델명**: ProcessdFile
- **DB 테이블명**: ProcessdFile
- **목적**: 업로드된 음성 파일과 STT 전사 결과를 저장

| 컬럼명 | Django 필드타입 | DB 타입 | 제약조건 | 설명 |
|--------|----------------|---------|----------|------|
| ocrn_no | CharField(max_length=50, primary_key=True) | VARCHAR(50) | PK | 발생번호 (UUID) |
| ocrn_hm | DateTimeField | DATETIME | NOT NULL | 발생시분 |
| trsc_file_nm | CharField(max_length=300, null=True, blank=True) | VARCHAR(300) | NULL | 전사파일명 |
| transcript | TextField | TEXT | NOT NULL | 전사내용 (STT 결과) |
| prcs_cont_1 | JSONField | JSON | NOT NULL | 1차 전처리내용 (ML 분석 결과) |
| prcs_cont_2 | JSONField(null=True, blank=True) | JSON | NULL | 2차 전처리내용 (DL 분석 결과) |
| vldtn_yn | CharField(max_length=1) | VARCHAR(1) | NOT NULL | 유효성 여부 ('Y'/'N') |
| stats_file_path | CharField(max_length=200) | VARCHAR(200) | NOT NULL | 통계파일경로 |
| file_path | CharField(max_length=200) | VARCHAR(200) | NOT NULL | 파일경로 (media/uploads/) |

### 3.2 InferenceResult - 추론 결과 테이블

- **Django 모델명**: InferenceResult
- **DB 테이블명**: InferenceResult
- **목적**: AI 모델의 추론 결과를 저장 (ML, DL, LLM 결과 포함)

| 컬럼명 | Django 필드타입 | DB 타입 | 제약조건 | 설명 |
|--------|----------------|---------|----------|------|
| id | AutoField | INTEGER | PK (자동증가) | Django 기본 ID |
| rslt_id | CharField(max_length=50) | VARCHAR(50) | NOT NULL | 결과ID (UUID) |
| ocrn_no | ForeignKey(ProcessdFile, on_delete=models.CASCADE) | VARCHAR(50) | FK | 발생번호 (ProcessdFile 참조) |
| mdl_id | CharField(max_length=20) | VARCHAR(20) | NOT NULL | 모델ID (ModelRegistry 참조) |
| file_id | CharField(max_length=50) | VARCHAR(50) | NOT NULL | 파일ID (길이 제한 고려) |
| prdt_scr | DecimalField(max_digits=4, decimal_places=3) | DECIMAL(4,3) | NOT NULL | 예측점수 (0.000-1.000) |
| ml_rslt_cd | CharField(max_length=10, choices=ML_RESULT_CHOICES) | VARCHAR(10) | NOT NULL | ML결과코드 ('0': 정상, '1': 피싱, '보류': 보류) |
| dl_jdgm_yn | CharField(max_length=1, null=True, blank=True) | VARCHAR(1) | NULL | DL판단여부 ('Y'/'N') |
| phsh_tp_nm | CharField(max_length=100) | VARCHAR(100) | NOT NULL | 피싱유형명 (LLM 생성) |
| warn_cn | TextField | TEXT | NOT NULL | 경고내용 (LLM 생성 메시지) |
| prdt_dt | DateTimeField | DATETIME | NOT NULL | 예측일시 |

**제약조건**:
- `unique_together = [['rslt_id', 'ocrn_no']]`
- `ML_RESULT_CHOICES = [('0', '정상'), ('1', '피싱'), ('보류', '보류')]`

### 3.3 ModelRegistry - 모델 레지스트리 테이블

- **Django 모델명**: ModelRegistry
- **DB 테이블명**: ModelRegistry
- **목적**: 시스템에 등록된 AI 모델 정보 관리

| 컬럼명 | Django 필드타입 | DB 타입 | 제약조건 | 설명 |
|--------|----------------|---------|----------|------|
| mdl_id | CharField(max_length=20, primary_key=True) | VARCHAR(20) | PK | 모델식별자 |
| mdl_nm | CharField(max_length=100) | VARCHAR(100) | NOT NULL | 모델명 |
| use_yn | CharField(max_length=1) | VARCHAR(1) | NOT NULL | 사용여부 ('Y'/'N') |

### 3.4 Feedback - 사용자 피드백 테이블

- **Django 모델명**: Feedback
- **DB 테이블명**: feedback
- **목적**: 사용자의 분석 결과 피드백 저장

| 컬럼명 | Django 필드타입 | DB 타입 | 제약조건 | 설명 |
|--------|----------------|---------|----------|------|
| id | AutoField | INTEGER | PK (자동증가) | Django 기본 ID |
| prp_no | CharField(max_length=20) | VARCHAR(20) | NOT NULL | 제안번호 (UUID 기반) |
| rslt_id | CharField(max_length=50) | VARCHAR(50) | NOT NULL | 결과ID (InferenceResult 참조) |
| ocrn_no | CharField(max_length=50) | VARCHAR(50) | NOT NULL | 발생번호 (ProcessdFile 참조) |
| prdt_rslt_yn | CharField(max_length=1) | VARCHAR(1) | NOT NULL | 예측결과여부 ('Y': 정확, 'N': 부정확) |
| wropn_cn | TextField(null=True, blank=True) | TEXT | NULL | 의견내용 (사용자 추가 의견) |
| opnn_reg_ymd | DateTimeField(null=True, blank=True) | DATETIME | NULL | 의견등록일시 |

**제약조건**:
- `unique_together = [['prp_no', 'rslt_id', 'ocrn_no']]`

### 3.5 VoicePhishingSystemLog - 상세 시스템 로그 테이블

- **Django 모델명**: VoicePhishingSystemLog
- **DB 테이블명**: SystemLog
- **목적**: 상세한 시스템 로깅 및 에러 추적 (업그레이드된 로깅 시스템)

| 컬럼명 | Django 필드타입 | DB 타입 | 제약조건 | 설명 |
|--------|----------------|---------|----------|------|
| id | AutoField | INTEGER | PK (자동증가) | Django 기본 ID |
| log_nm | CharField(max_length=300) | VARCHAR(300) | NOT NULL | 로그명 (상세한 로그 식별자) |
| ocrn_no | ForeignKey(ProcessdFile, on_delete=models.CASCADE) | VARCHAR(50) | FK | 발생번호 (ProcessdFile 참조) |
| err_no | CharField(max_length=20, null=True, blank=True) | VARCHAR(20) | NULL | 에러번호 (시스템 정의 에러 코드) |
| log_reg_dt | DateTimeField | DATETIME | NOT NULL | 로그등록일시 |
| log_ocrn_pstn | CharField(max_length=200) | VARCHAR(200) | NOT NULL | 로그발생위치 (파일명:라인번호) |
| err_rsn | TextField(null=True, blank=True) | TEXT | NULL | 에러사유 (상세 에러 메시지) |
| err_cd_nm | CharField(max_length=300, null=True, blank=True) | VARCHAR(300) | NULL | 에러코드명 (에러 분류명) |

**제약조건**:
- `unique_together = [['log_nm', 'ocrn_no']]`

### 3.6 SystemLog - 기존 호환성 시스템 로그 테이블

- **Django 모델명**: SystemLog
- **DB 테이블명**: system_logs
- **목적**: 기존 시스템과의 호환성을 위한 범용 로깅 (INFO, WARNING, ERROR, CRITICAL)

| 컬럼명 | Django 필드타입 | DB 타입 | 제약조건 | 설명 |
|--------|----------------|---------|----------|------|
| id | AutoField | INTEGER | PK (자동증가) | Django 기본 ID |
| level | CharField(max_length=10, choices=LOG_LEVELS) | VARCHAR(10) | NOT NULL | 로그레벨 (INFO, WARNING, ERROR, CRITICAL) |
| message | TextField | TEXT | NOT NULL | 로그메시지 |
| file_name | CharField(max_length=255, null=True, blank=True) | VARCHAR(255) | NULL | 관련 파일명 |
| ip_address | GenericIPAddressField(null=True, blank=True) | INET | NULL | 클라이언트 IP 주소 |
| created_at | DateTimeField(default=timezone.now) | DATETIME | NOT NULL | 생성일시 |

**제약조건**:
- `ordering = ['-created_at']` (최신순 정렬)
- `LOG_LEVELS = [('INFO', 'Info'), ('WARNING', 'Warning'), ('ERROR', 'Error'), ('CRITICAL', 'Critical')]`

### 3.7 AnalysisResult - UI 호환용 분석 결과 테이블

- **Django 모델명**: AnalysisResult
- **DB 테이블명**: voice_phishing_results
- **목적**: 기존 UI와의 호환성을 위한 분석 결과 저장

| 컬럼명 | Django 필드타입 | DB 타입 | 제약조건 | 설명 |
|--------|----------------|---------|----------|------|
| id | AutoField | INTEGER | PK (자동증가) | Django 기본 ID |
| file_name | CharField(max_length=255) | VARCHAR(255) | NOT NULL | 파일명 (길이 제한 적용) |
| file_size | IntegerField | INTEGER | NOT NULL | 파일 크기 (bytes) |
| file_type | CharField(max_length=50) | VARCHAR(50) | NOT NULL | 파일 타입 (MIME type) |
| is_phishing | BooleanField | BOOLEAN | NOT NULL | 보이스피싱 여부 |
| confidence | FloatField | FLOAT | NOT NULL | 신뢰도 (0.0-1.0) |
| phishing_type | CharField(max_length=50, null=True, blank=True) | VARCHAR(50) | NULL | 피싱 유형 |
| stt_text | TextField(null=True, blank=True) | TEXT | NULL | STT 변환 텍스트 |
| risk_factors | JSONField(default=list) | JSON | NOT NULL | 위험 요소 배열 |
| explanation | TextField(null=True, blank=True) | TEXT | NULL | 분석 설명 |
| warning_message | TextField(null=True, blank=True) | TEXT | NULL | 경고 메시지 |
| created_at | DateTimeField(default=timezone.now) | DATETIME | NOT NULL | 생성일시 |
| processing_time | FloatField(null=True, blank=True) | FLOAT | NULL | 처리 시간(초) |
| ip_address | GenericIPAddressField(null=True, blank=True) | INET | NULL | 클라이언트 IP 주소 |

**제약조건**:
- `ordering = ['-created_at']` (최신순 정렬)

## 4. 도메인 정의서 (Django 기반)

공통적으로 사용되는 데이터 타입이나 선택지들을 도메인으로 정의합니다.

| 도메인명 | Django 구현 | 데이터 타입 | 설명 |
|----------|------------|-------------|------|
| ML_RESULT_CHOICES | [('0', '정상'), ('1', '피싱'), ('보류', '보류')] | VARCHAR(10) | ML 예측 결과 코드 |
| LOG_LEVELS | [('INFO', 'Info'), ('WARNING', 'Warning'), ('ERROR', 'Error'), ('CRITICAL', 'Critical')] | VARCHAR(10) | 시스템 로그 레벨 |
| 여부_도메인 | 'Y' 또는 'N' | CHAR(1) | 예/아니오 여부 ('Y': 예, 'N': 아니오) |
| 예측점수_도메인 | DecimalField(max_digits=4, decimal_places=3) | DECIMAL(4,3) | 예측점수 (0.000~1.000) |
| UUID_도메인 | CharField(max_length=50) | VARCHAR(50) | UUID 기반 식별자 |
| IP주소_도메인 | GenericIPAddressField | INET | IPv4/IPv6 주소 |

## 5. 제약조건 및 관계 정의 (Django ORM 기반)

Django ORM을 통한 테이블 간의 관계 및 제약조건을 정의합니다.

### 5.1 Foreign Key 관계

| 관계명 | 소스 모델.필드 | 타겟 모델 | 관계 타입 | 삭제 규칙 | 설명 |
|--------|----------------|-----------|-----------|----------|------|
| InferenceResult → ProcessdFile | InferenceResult.ocrn_no | ProcessdFile | ForeignKey | CASCADE | 추론 결과의 파일 참조 |
| VoicePhishingSystemLog → ProcessdFile | VoicePhishingSystemLog.ocrn_no | ProcessdFile | ForeignKey | CASCADE | 시스템 로그의 파일 참조 |

### 5.2 참조 관계 (문자열 기반)

| 관계명 | 소스 필드 | 타겟 모델 | 참조 필드 | 설명 |
|--------|-----------|-----------|-----------|------|
| InferenceResult → ModelRegistry | InferenceResult.mdl_id | ModelRegistry | mdl_id | 모델 식별자 참조 |
| Feedback → InferenceResult | Feedback.rslt_id | InferenceResult | rslt_id | 피드백의 추론 결과 참조 |
| Feedback → ProcessdFile | Feedback.ocrn_no | ProcessdFile | ocrn_no | 피드백의 파일 참조 |

### 5.3 Unique 제약조건

| 테이블 | 제약조건 | 설명 |
|--------|----------|------|
| InferenceResult | unique_together = [['rslt_id', 'ocrn_no']] | 결과ID와 발생번호 조합의 유일성 |
| Feedback | unique_together = [['prp_no', 'rslt_id', 'ocrn_no']] | 제안번호, 결과ID, 발생번호 조합의 유일성 |
| VoicePhishingSystemLog | unique_together = [['log_nm', 'ocrn_no']] | 로그명과 발생번호 조합의 유일성 |

### 5.4 인덱스 및 정렬

| 테이블 | 인덱스/정렬 | 설명 |
|--------|-------------|------|
| SystemLog | ordering = ['-created_at'] | 생성일시 역순 정렬 (최신순) |
| AnalysisResult | ordering = ['-created_at'] | 생성일시 역순 정렬 (최신순) |

## 6. 데이터베이스 마이그레이션 정보

Django 마이그레이션 파일들을 통한 스키마 버전 관리:

| 마이그레이션 파일 | 설명 |
|-------------------|------|
| 0001_initial.py | 초기 테이블 생성 |
| 0002_modelregistry_processdfile_alter_systemlog_options_and_more.py | ModelRegistry, ProcessdFile 추가 및 SystemLog 옵션 변경 |
| 0003_alter_inferenceresult_file_id.py | InferenceResult.file_id 필드 변경 |
| 0004_fix_inferenceresult_file_id_length.py | InferenceResult.file_id 길이 제한 수정 |
| 0005_populate_model_registry.py | ModelRegistry 초기 데이터 입력 |

## 7. 데이터베이스 사용 패턴

### 7.1 분석 프로세스 데이터 흐름

#### 메인 프로세스
1. **파일 업로드** → ProcessdFile 생성 (고유 ocrn_no 생성, STT 결과 저장)
2. **1차 AI 분석** → ProcessdFile.prcs_cont_1 업데이트 (ML 모델 결과)
3. **2차 AI 분석** → ProcessdFile.prcs_cont_2 업데이트 (DL 모델 결과)
4. **종합 추론** → InferenceResult 생성 (ML, DL, LLM 통합 결과)
5. **UI 호환성** → AnalysisResult 생성 (기존 시스템 호환)

#### 부가 프로세스
6. **사용자 피드백** → Feedback 생성 (분석 결과 검증)
7. **상세 로깅** → VoicePhishingSystemLog 생성 (프로세스별 로그)
8. **일반 로깅** → SystemLog 생성 (시스템 전반 로그)

#### 데이터 연관성
- 모든 테이블은 ocrn_no(발생번호)를 통해 연관
- InferenceResult는 mdl_id를 통해 ModelRegistry와 연관
- 트랜잭션 단위로 데이터 정합성 보장

### 7.2 통계 쿼리 패턴

#### 기본 통계
- **총 분석 건수**: `ProcessdFile.objects.count()`
- **성공적 분석 건수**: `ProcessdFile.objects.filter(vldtn_yn='Y').count()`
- **실패한 분석 건수**: `ProcessdFile.objects.filter(vldtn_yn='N').count()`

#### 추론 결과 통계 (InferenceResult 기준)
- **피싱 탐지 건수**: `InferenceResult.objects.filter(ml_rslt_cd='1').count()`
- **정상 통화 건수**: `InferenceResult.objects.filter(ml_rslt_cd='0').count()`
- **보류 건수**: `InferenceResult.objects.filter(ml_rslt_cd='보류').count()`
- **피싱 탐지율**: (피싱 탐지 건수 / 총 추론 건수) * 100

#### 호환성 통계 (AnalysisResult 기준, Legacy UI용)
- **UI 호환 피싱 탐지**: `AnalysisResult.objects.filter(is_phishing=True).count()`
- **UI 호환 정상 통화**: `AnalysisResult.objects.filter(is_phishing=False).count()`

#### 피드백 통계
- **정확한 예측**: `Feedback.objects.filter(prdt_rslt_yn='Y').count()`
- **부정확한 예측**: `Feedback.objects.filter(prdt_rslt_yn='N').count()`
- **예측 정확도**: (정확한 예측 / 총 피드백) * 100

#### 모델별 성능 통계
```python
from django.db.models import Count, Avg
model_stats = InferenceResult.objects.values('mdl_id').annotate(
    total_predictions=Count('rslt_id'),
    avg_confidence=Avg('prdt_scr')
)
```

### 7.3 데이터 정합성 보장

#### 트랜잭션 처리

```python
from django.db import transaction

@transaction.atomic
def save_analysis_result(file_data, analysis_data):
    # ProcessdFile, InferenceResult, AnalysisResult 동시 저장
    pass
```

#### 데이터 검증
- Django 모델 validators 사용
- 커스텀 clean() 메서드로 추가 검증
- 데이터베이스 제약조건과 애플리케이션 레벨 검증 이중화

## 8. 성능 최적화 고려사항

### 8.1 인덱스 전략

- **created_at 필드**: 시간 기반 조회를 위한 인덱스 (Django 자동 생성)
- **is_phishing 필드**: 통계 쿼리 최적화를 위한 인덱스 고려
- **ip_address 필드**: 사용자 추적을 위한 인덱스 고려

### 8.2 쿼리 최적화

#### N+1 쿼리 문제 해결

```python
# Bad
results = InferenceResult.objects.all()
for result in results:
    print(result.ocrn_no.file_path)  # N+1 query

# Good  
results = InferenceResult.objects.select_related('ocrn_no').all()
```

#### 대용량 데이터 처리

```python
# 배치 처리
for batch in queryset.iterator(chunk_size=1000):
    process_batch(batch)
```

### 8.3 데이터 아카이빙

- **SystemLog**: 로그 레벨별 보관 정책 고려
- **AnalysisResult**: 분석 결과의 장기 보관 정책 수립
- **미디어 파일**: media/uploads/ 디렉토리 용량 관리

## 9. 보안 고려사항

### 9.1 데이터 보호

- **IP 주소**: 개인정보 보호를 위한 마스킹 고려
- **음성 파일**: 업로드 파일의 보안 저장
- **STT 결과**: 민감 정보 필터링 고려

### 9.2 접근 제어

- **Django Admin**을 통한 데이터베이스 접근 제어
- **로그 데이터**의 접근 권한 관리
- **피드백 데이터**의 익명화 처리

### 9.3 SQL 인젝션 방지

```python
# Safe (Django ORM)
users = User.objects.filter(name=user_input)

# Unsafe (Raw SQL)
cursor.execute("SELECT * FROM users WHERE name = '%s'" % user_input)
```

## 10. 백업 및 복구 전략

### 10.1 백업 정책

| 데이터 유형 | 백업 주기 | 보관 기간 | 백업 방법 |
|-------------|----------|----------|----------|
| 운영 데이터베이스 | 일일 | 30일 | mysqldump + 압축 |
| 시스템 로그 | 주간 | 90일 | 파일 압축 아카이브 |
| 사용자 피드백 | 일일 | 영구 | 별도 백업 스토리지 |
| AI 모델 파일 | 월간 | 영구 | Git LFS + 클라우드 |

### 10.2 복구 절차

#### 데이터베이스 복구

```bash
# 백업 복구
mysql -u username -p database_name < backup_file.sql

# Django 마이그레이션 재적용
python manage.py migrate
```

#### 데이터 무결성 확인

```bash
# Django 관리 명령어로 데이터 검증
python manage.py check_data_integrity
```

## 11. 모니터링 및 알림

### 11.1 데이터베이스 모니터링

#### 성능 지표
- 쿼리 응답 시간
- 동시 연결 수
- 저장 공간 사용률
- 슬로우 쿼리 로그

#### 알림 설정
- 데이터베이스 연결 실패
- 디스크 용량 80% 초과
- 슬로우 쿼리 임계값 초과
- 백업 실패

### 11.2 데이터 품질 모니터링

#### 일일 체크리스트
- 데이터 중복 검사
- 필수 필드 NULL 값 확인
- 외래키 무결성 검증
- JSON 필드 스키마 검증

## 12. 버전 정보 및 변경 이력

### v4.0 (2025.08.01) - 최종 구현 버전

- 실제 Django 모델과 100% 일치하도록 전면 개정
- 6개 모델 (ProcessdFile, InferenceResult, ModelRegistry, Feedback, SystemLog, AnalysisResult) 완전 문서화
- Django ORM 관계 및 제약조건 정확히 반영
- 마이그레이션 파일 정보 추가
- 데이터베이스 사용 패턴 및 성능 최적화 가이드 추가
- 백업/복구 전략 및 모니터링 가이드 추가

### v3.0 (2025.07.17) - 초기 설계 버전

- 기본 테이블 구조 정의

### v2.0 (2025.07.17) - 초기 설계 버전

- 기본 테이블 구조 정의