# 프로젝트 개요
이 프로젝트는 보이스 피싱 근절을 위해 보이스 피싱 텍스트 데이터로 학습시킨 ML모델1과 DL모델2를 사용하여 보이스피싱 판별하여  
판별 결과와 음성 파일 내용에 따라 LLM을 사용하여 보이스 피싱일 경우 사용자에게 적절한 경고 문구를 출력하는 프로그램을 완성 하는 것  

# 주요 목표
- 구해온 보이스피싱과 일반 전화음성 데이터를 TTS를 사용하여 텍스트화 시킨다.(화자 분리도 되어야함.)
- LLM과 LANG CHAIN을 통해서 적절한 프롬프트를 작성하여 부족한 보이스 피싱 데이터를 증강한다.
- 텍스트화된 데이터들을 ML과 DL의 학습에 알맞게 데이터셋으로 만든다.
- ML과 DL을 적절한 데이터를 넣어 학습시킨다.
- Django를 사용하여 웹페이지를 만들고 사용자가 음성파일을 로드하는 부분에 넣으면 보이스피싱을 판별하게  
하는 front end와 back end를 만든다.
- 보이스 피싱으로 판별된다면 LLM을 사용하여 로드된 음성데이터를 읽어 적절한 대응방안을 제시해준다.



# 기술 스택
- "ipykernel>=6.29.5",
- "jpype1>=1.5.2",
- "jupyterlab>=4.4.4",
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
- "xgboost>=3.0.2",


# 주요 명령어



# 코딩 스타일


# 커밋 메시지 규칙



# 프로젝트 구조
- `dataset/`: 모델 학습에 사용되는 원본 데이터셋
- `dataset_create/`: 데이터셋을 가공하고 생성하는 Jupyter Notebook 파일들