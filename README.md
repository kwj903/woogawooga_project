# woogawooga_project
* 데이터 분석 개발자 교육 과정 4조 프로젝트(우가우가), 조원: 우재, 진주, 영재, 채연

# 프로젝트 개요
Django 기반 보이스피싱 탐지 시스템 - 음성 데이터를 분석하여 보이스피싱을 탐지하고 사용자에게 안전성을 알려주는 웹 애플리케이션

## 시스템 아키텍처

### 음성 분석 파이프라인
1. **음성 처리 단계**
   - STT(Speech-to-Text): VITO STT API를 활용한 한국어 음성 인식
   - 지원 파일: MP3, WAV, AMR, M4A (최대 50MB)
   - 실시간 진행상황: WebSocket 기반 프로그레스 업데이트

2. **텍스트 전처리**
   - 형태소 분석: KiWi(Korean Intelligent Word Identifier) 사용
   - 특성 추출: 명사(NNG, NNP)와 동사/형용사(VV, VA) 추출
   - 텍스트 정규화: 동사/형용사에 "다" 어미 추가

3. **2단계 ML 분석 파이프라인**
   - 1단계: Stacking 앙상블 + 임계값 기반 라우팅
   - 2단계: 애매한 케이스를 위한 딥러닝 앙상블
   - 최종 단계: GPT-4 기반 설명 생성

### 사용 모델
- **주요 모델**: `stacking_v2.pkl` - Stacking 앙상블 (LightGBM + SVM + Logistic Regression)
- **보조 모델**: `mBERT_ensemble_detector.pkl` - 애매한 케이스 처리용 앙상블
- **LLM 통합**: OpenAI GPT-4로 상황별 경고 및 설명 생성
- **NLP**: KiWi 형태소 분석기, TF-IDF 벡터화

### 탐지 방식
- **다단계 의사결정**: 신뢰도 기반 단계별 분석 (≤30% 정상, ≥75% 피싱, 30-75% 보류→2단계)
- **보이스피싱 유형 분류**: 기관사칭형, 지인사칭형, 택배사칭형, 대출빙자형, 투자빙자형 등 7개 유형
- **실시간 분석**: WebSocket 기반 비동기 처리

# 현재 설치한 라이브러리 : 
- requires-python = ">=3.10"
- "google-genai>=1.24.0",
- "google-generativeai>=0.8.5",
- "ipykernel>=6.29.5",
- "jpype1>=1.5.2",
- "jupyterlab>=4.4.4",
- "kiwipiepy>=0.21.0",
- "konlpy>=0.6.0",
- "koreanize-matplotlib>=0.1.1",
- "langchain>=0.3.26",
- "langchain-openai>=0.3.27",
- "langchain-pinecone>=0.2.8",
- "lightgbm>=4.6.0",
- "matplotlib>=3.10.3",
- "nltk>=3.9.1",
- "notebook>=7.4.4",
- "numpy>=2.2.6",
- "openai-whisper",
- "opencv-contrib-python>=4.11.0.86",
- "pandas>=2.3.0",
- "pinecone-client>=6.0.0",
- "pyannote-audio",
- "python-dotenv>=1.1.1",
- "requests>=2.32.4",
- "scikit-learn>=1.7.0",
- "scipy>=1.15.3",
- "seaborn>=0.13.2",
- "selenium>=4.34.0",
- "torch>=2.7.1",
- "torchvision>=0.22.1",
- "webdriver-manager>=4.0.2",
- "whisperx>=3.4.2",
- "wordcloud>=1.9.4",
- "xgboost>=3.0.2",
# 작업 폴더 설정
## dataset_create 작업 폴더 : 데이터셋 준비하는 작업 폴더


