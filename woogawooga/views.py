from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import (
    AnalysisResult, SystemLog, ProcessdFile, InferenceResult, 
    ModelRegistry, Feedback, VoicePhishingSystemLog
)
from .consumers import send_progress_update, send_analysis_complete, send_analysis_error
import json
import time
import random
import logging
import uuid
import pickle
import joblib
import os
from pathlib import Path
import numpy as np
from datetime import datetime
import requests
import tempfile
from django.conf import settings

# 로거 설정
logger = logging.getLogger(__name__)

# 터미널 출력을 위한 헬퍼 함수들
def log_and_print(level, message):
    """로깅과 프린트를 동시에 수행하는 함수 (한글 인코딩 문제 해결)"""
    try:
        # 로깅 수행
        if level.upper() == 'INFO':
            logger.info(message)
        elif level.upper() == 'WARNING':
            logger.warning(message)
        elif level.upper() == 'ERROR':
            logger.error(message)
        elif level.upper() == 'DEBUG':
            logger.debug(message)
        
        # 터미널에 직접 출력 (UTF-8 인코딩 보장)
        print(f"[{level.upper()}] {message}", flush=True)
        
    except UnicodeEncodeError:
        # 인코딩 문제 발생 시 영어로 대체
        safe_message = message.encode('ascii', errors='ignore').decode('ascii')
        print(f"[{level.upper()}] {safe_message} [ENCODING_ERROR]", flush=True)
        if level.upper() == 'INFO':
            logger.info(safe_message + " [ENCODING_ERROR]")
        elif level.upper() == 'WARNING':
            logger.warning(safe_message + " [ENCODING_ERROR]")
        elif level.upper() == 'ERROR':
            logger.error(safe_message + " [ENCODING_ERROR]")

def print_separator():
    """구분선 출력"""
    separator = "=" * 80
    print(separator, flush=True)
    logger.info(separator)

# 서버 시작 시 로깅 테스트
print_separator()
log_and_print("INFO", "[STARTUP] WOOGAWOOGA App Load Complete")
log_and_print("INFO", "   Logging System Activated")
log_and_print("INFO", f"   Logger Name: {logger.name}")
log_and_print("INFO", f"   Log Level: {logger.level}")
log_and_print("INFO", f"   Handler Count: {len(logger.handlers)}")
print_separator()

# 로깅 테스트 함수들
def test_logging_levels():
    log_and_print("DEBUG", "[DEBUG] DEBUG Level Test")
    log_and_print("INFO", "[INFO] INFO Level Test")
    log_and_print("WARNING", "[WARNING] WARNING Level Test")
    log_and_print("ERROR", "[ERROR] ERROR Level Test")

# 앱 로드 시 로깅 레벨 테스트 실행
test_logging_levels()

# 머신러닝 및 자연어 처리
try:
    from kiwipiepy import Kiwi
    import lightgbm as lgb
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from transformers import AutoTokenizer, AutoModel
    from torch.utils.data import Dataset, DataLoader
    logger.info("머신러닝 패키지 import 완료")
except ImportError as e:
    logger.warning(f"필수 패키지 import 실패: {e}")

def refresh_vito_token():
    """VITO API 토큰 갱신"""
    try:
        client_id = os.getenv('CLIENT_ID')
        client_secret = os.getenv('CLIENT_SECRET')
        
        if not client_id or not client_secret:
            logger.error("VITO CLIENT_ID 또는 CLIENT_SECRET이 없음")
            return None
            
        # VITO 토큰 발급 API 호출
        auth_url = "https://openapi.vito.ai/v1/authenticate"
        auth_data = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        response = requests.post(auth_url, json=auth_data, timeout=30)
        
        if response.status_code == 200:
            token_data = response.json()
            new_token = token_data.get('access_token')
            
            if new_token:
                logger.info("VITO 토큰 갱신 성공")
                # 환경변수 업데이트 (현재 세션에서만)
                os.environ['VITO_API_KEY'] = new_token
                return new_token
            else:
                logger.error("VITO 응답에서 access_token을 찾을 수 없음")
                return None
        else:
            logger.error(f"VITO 토큰 갱신 실패: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"VITO 토큰 갱신 오류: {e}")
        return None

# 로깅 설정은 Django settings.py에서 관리됩니다

# KoBERT 기반 PyTorch 모델 클래스 정의
class TextOnlyPhishingDetector(nn.Module):
    def __init__(self, bert_model_name='skt/kobert-base-v1', hidden_dim=128, num_classes=2, dropout_rate=0.3):
        super(TextOnlyPhishingDetector, self).__init__()
        
        # KoBERT 모델 로드
        self.bert = AutoModel.from_pretrained(bert_model_name)
        self.bert_hidden_size = self.bert.config.hidden_size  # 768
        
        # LSTM 층
        self.lstm = nn.LSTM(
            input_size=self.bert_hidden_size,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=dropout_rate,
            bidirectional=True
        )
        
        # Attention 층
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim * 2,  # bidirectional
            num_heads=8,
            dropout=dropout_rate,
            batch_first=True
        )
        
        # 분류 층 (저장된 모델과 일치하도록 구조 수정)
        self.classifier = nn.Sequential(
            nn.Dropout(dropout_rate),           # 0
            nn.Linear(hidden_dim * 2, hidden_dim), # 1
            nn.ReLU(),                          # 2
            nn.Dropout(dropout_rate),           # 3
            nn.Linear(hidden_dim, num_classes)  # 4
        )
        
    def forward(self, input_ids, attention_mask):
        # BERT 인코딩
        bert_outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = bert_outputs.last_hidden_state  # [batch_size, seq_len, hidden_size]
        
        # LSTM 처리
        lstm_output, (hidden, cell) = self.lstm(sequence_output)  # [batch_size, seq_len, hidden_dim * 2]
        
        # Attention 적용
        attn_output, _ = self.attention(lstm_output, lstm_output, lstm_output)
        
        # Global average pooling
        pooled_output = torch.mean(attn_output, dim=1)  # [batch_size, hidden_dim * 2]
        
        # 분류
        logits = self.classifier(pooled_output)
        
        return logits

# 대화 데이터셋 클래스
class DialogueDataset(Dataset):
    def __init__(self, texts, tokenizer, max_length=128):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        
        # 토크나이징
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten()
        }

# 모델 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / 'models' / 'stacking_v2.pkl'
PYTORCH_MODEL_PATH = BASE_DIR / 'models' / 'kobert_2nd_model_runpod.pth'  # 2차 KoBERT 모델
LGBM_MODEL_PATH = BASE_DIR / 'models' / 'lgbm_model_v2.pkl'  # 기존 LightGBM (백업용)
TFIDF_PATH = BASE_DIR / 'datas' / 'modelsData' / 'tfidf_vectorizer.pkl'

# 모델 전역 변수
stacking_model = None  # 1차 Pipeline 모델 (TF-IDF + Stacking)
pytorch_model = None  # KoBERT 기반 2차 모델
kobert_tokenizer = None  # KoBERT 토크나이저
lgbm_model = None  # 백업용 (deprecated)
kiwi_tokenizer = None  # 키위 토크나이저

def load_models():
    """모든 필수 모델 및 토크나이저 로드"""
    global stacking_model, pytorch_model, kobert_tokenizer, lgbm_model, kiwi_tokenizer
    
    try:
        # 1차 Stacking Pipeline 모델 로드
        if stacking_model is None and MODEL_PATH.exists():
            try:
                logger.info(f"1차 Pipeline 모델 로드 시도: {MODEL_PATH}")
                
                # joblib 사용 (scikit-learn Pipeline에 권장)
                stacking_model = joblib.load(MODEL_PATH)
                logger.info("1차 Pipeline 모델 로드 성공")
                logger.info(f"모델 타입: {type(stacking_model).__name__}")
                
                # Pipeline 구조 확인
                if hasattr(stacking_model, 'steps'):
                    logger.info(f"Pipeline 단계: {[step[0] for step in stacking_model.steps]}")
                    
            except Exception as e:
                logger.error(f"1차 Pipeline 모델 로드 실패: {e}")
                logger.error(f"파일 경로: {MODEL_PATH}")
        elif not MODEL_PATH.exists():
            logger.warning(f"1차 모델 파일 없음: {MODEL_PATH}")
        
        # 2차 PyTorch KoBERT 모델 로드
        if pytorch_model is None and PYTORCH_MODEL_PATH.exists():
            try:
                logger.info(f"2차 PyTorch 모델 로드 시도: {PYTORCH_MODEL_PATH}")
                
                # 파일 크기 검증
                file_size = PYTORCH_MODEL_PATH.stat().st_size
                logger.info(f"PyTorch 모델 파일 크기: {file_size} bytes")
                
                if file_size < 1000:  # 너무 작은 파일
                    logger.error(f"PyTorch 모델 파일이 너무 작음: {file_size} bytes")
                else:
                    # 모델 인스턴스 생성
                    pytorch_model = TextOnlyPhishingDetector()
                    
                    # GPU 사용 가능하면 GPU로, 아니면 CPU로
                    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                    
                    # 모델 가중치 로드 (weights_only=False로 설정)
                    checkpoint = torch.load(PYTORCH_MODEL_PATH, map_location=device, weights_only=False)
                    
                    # 체크포인트 구조 확인 및 적절한 state_dict 추출
                    if isinstance(checkpoint, dict):
                        logger.info(f"체크포인트 키들: {list(checkpoint.keys())}")
                        
                        if 'model_state_dict' in checkpoint:
                            # 훈련 시 저장된 전체 체크포인트에서 모델 state_dict 추출
                            state_dict = checkpoint['model_state_dict']
                            logger.info("체크포인트에서 model_state_dict 추출")
                            
                            # 모델 구조 정보 확인
                            if 'model_config' in checkpoint:
                                config = checkpoint['model_config']
                                logger.info(f"저장된 모델 설정: {config}")
                                
                                # 저장된 설정에 따라 모델 재생성
                                if isinstance(config, dict):
                                    bert_model_name = config.get('bert_model_name', 'skt/kobert-base-v1')
                                    hidden_dim = config.get('hidden_dim', 128)
                                    num_classes = config.get('num_classes', 2)
                                    dropout_rate = config.get('dropout_rate', 0.3)
                                    
                                    logger.info(f"저장된 설정으로 모델 재생성: bert={bert_model_name}, hidden={hidden_dim}")
                                    pytorch_model = TextOnlyPhishingDetector(
                                        bert_model_name=bert_model_name,
                                        hidden_dim=hidden_dim,
                                        num_classes=num_classes,
                                        dropout_rate=dropout_rate
                                    )
                            
                            # 추가 정보 로깅
                            if 'training_info' in checkpoint:
                                logger.info(f"훈련 정보: {checkpoint['training_info']}")
                            
                            # state_dict의 키 구조 확인
                            sample_keys = list(state_dict.keys())[:10]
                            logger.info(f"state_dict 샘플 키들: {sample_keys}")
                            
                        else:
                            # 직접 state_dict인 경우
                            state_dict = checkpoint
                            logger.info("직접 state_dict 사용")
                            logger.info(f"직접 state_dict 키들: {list(state_dict.keys())[:10]}")
                    else:
                        # 모델 객체 자체인 경우
                        state_dict = checkpoint.state_dict()
                        logger.info("모델 객체에서 state_dict 추출")
                    
                    # state_dict 로드 시도 (strict=False로 부분 로딩 허용)
                    try:
                        pytorch_model.load_state_dict(state_dict, strict=True)
                        logger.info("state_dict 완전 로드 성공")
                    except RuntimeError as e:
                        logger.warning(f"완전 로드 실패, 부분 로드 시도: {e}")
                        # 부분 로드 시도
                        missing_keys, unexpected_keys = pytorch_model.load_state_dict(state_dict, strict=False)
                        logger.warning(f"누락된 키 개수: {len(missing_keys)}")
                        logger.warning(f"예상치 못한 키 개수: {len(unexpected_keys)}")
                        
                        if len(missing_keys) > 10:  # 너무 많은 키가 누락되면
                            logger.error("너무 많은 키가 누락됨. 모델 구조가 완전히 다름")
                            
                            # 상세 키 분석
                            logger.error("=== 상세 키 분석 ===")
                            logger.error(f"누락된 키 (처음 10개): {missing_keys[:10]}")
                            logger.error(f"예상치 못한 키 (처음 10개): {unexpected_keys[:10]}")
                            
                            # 저장된 모델의 실제 키 패턴 분석
                            bert_keys = [k for k in state_dict.keys() if 'bert' in k]
                            lstm_keys = [k for k in state_dict.keys() if 'lstm' in k]
                            attention_keys = [k for k in state_dict.keys() if 'attention' in k]
                            classifier_keys = [k for k in state_dict.keys() if 'classifier' in k]
                            
                            logger.error(f"저장된 BERT 키들: {bert_keys[:5]}")
                            logger.error(f"저장된 LSTM 키들: {lstm_keys}")
                            logger.error(f"저장된 Attention 키들: {attention_keys}")
                            logger.error(f"저장된 Classifier 키들: {classifier_keys}")
                            
                            # 우리 모델의 키 패턴
                            our_keys = list(pytorch_model.state_dict().keys())
                            our_bert_keys = [k for k in our_keys if 'bert' in k]
                            our_lstm_keys = [k for k in our_keys if 'lstm' in k]
                            our_attention_keys = [k for k in our_keys if 'attention' in k]
                            our_classifier_keys = [k for k in our_keys if 'classifier' in k]
                            
                            logger.error(f"우리 BERT 키들: {our_bert_keys[:5]}")
                            logger.error(f"우리 LSTM 키들: {our_lstm_keys}")
                            logger.error(f"우리 Attention 키들: {our_attention_keys}")
                            logger.error(f"우리 Classifier 키들: {our_classifier_keys}")
                            
                            # 부분 로드라도 시도해봄 (핵심 키만)
                            logger.warning("부분 로드로 계속 진행...")
                    pytorch_model.to(device)
                    pytorch_model.eval()  # 추론 모드로 설정
                    
                    logger.info(f"2차 PyTorch 모델 로드 완료 (device: {device})")
                    
            except Exception as e:
                logger.error(f"PyTorch 모델 로드 실패: {e}")
                logger.error(f"파일 경로: {PYTORCH_MODEL_PATH}")
                logger.error(f"오류 타입: {type(e).__name__}")
        elif not PYTORCH_MODEL_PATH.exists():
            logger.warning(f"2차 PyTorch 모델 파일 없음: {PYTORCH_MODEL_PATH}")
        
        # KoBERT 토크나이저 로드
        if kobert_tokenizer is None:
            try:
                kobert_tokenizer = AutoTokenizer.from_pretrained('skt/kobert-base-v1')
                logger.info("KoBERT 토크나이저 로드 완료")
            except Exception as e:
                logger.error(f"KoBERT 토크나이저 로드 실패: {e}")
        
        # 2차 LightGBM 모델 로드 (백업용 - 더 이상 사용하지 않음)
        if lgbm_model is None and LGBM_MODEL_PATH.exists():
            try:
                lgbm_model = lgb.Booster(model_file=str(LGBM_MODEL_PATH))
                logger.info("2차 LightGBM 모델 (백업용) 로드 완료")
            except Exception as e:
                logger.error(f"LightGBM 모델 로드 실패: {e}")
        elif not LGBM_MODEL_PATH.exists():
            logger.warning(f"백업용 LightGBM 모델 파일 없음: {LGBM_MODEL_PATH}")
        
        # ❌ TF-IDF 벡터라이저 로드 제거
        # 1차 모델이 Pipeline 구조로 내부에 TF-IDF가 포함되어 있으므로 별도 로딩 불필요
        logger.info("TF-IDF 벡터라이저는 1차 Pipeline 모델에 포함되어 있으므로 별도 로딩하지 않음")
        
        # KiWi 토크나이저 초기화
        if kiwi_tokenizer is None:
            try:
                kiwi_tokenizer = Kiwi()
                logger.info("KiWi 토크나이저 초기화 완료")
            except Exception as e:
                logger.error(f"KiWi 토크나이저 초기화 실패: {e}")
                
    except Exception as e:
        logger.error(f"모델 로드 중 전체 오류: {str(e)}")

def tokenize_and_filter(text):
    """노트북과 동일한 토큰화 함수 - KiWi를 사용한 텍스트 전처리"""
    try:
        # 모델 로드 확인
        if not kiwi_tokenizer:
            load_models()
        
        if not kiwi_tokenizer:
            logger.warning("KiWi 토크나이저가 없어서 기본 분할 사용")
            return text
        
        # KiWi로 형태소 분석 (노트북과 동일한 방식)
        result = kiwi_tokenizer.analyze(text)[0][0]
        tokens = []
        
        for word, pos, _, _ in result:
            # 노트북과 동일한 조건: NNG, NNP, VV, VA만 추출
            if pos in {"NNG", "NNP", "VV", "VA"}:
                # 동사, 형용사에 "다" 추가 (노트북과 동일)
                if pos in {"VV", "VA"}:
                    word = word + "다"
                tokens.append(word)
        
        processed_text = " ".join(tokens)
        logger.info(f"토큰화 완료: 원본 길이={len(text)}, 토큰 수={len(tokens)}")
        
        return processed_text
        
    except Exception as e:
        logger.error(f"토큰화 실패: {str(e)}")
        return text

def preprocess_text(text):
    """기존 호환성을 위한 래퍼 함수"""
    processed_text = tokenize_and_filter(text)
    
    # 기존 반환 형식 유지
    return {
        "tokens": processed_text.split() if processed_text else [],
        "vector": [],  # Pipeline 모델에서는 사용하지 않음
        "processed_text": processed_text
    }

def vito_stt(audio_file):
    """VITO STT API를 사용한 음성 인식"""
    try:
        # API 키 확인
        api_key = getattr(settings, 'VITO_API_KEY', None)
        if not api_key:
            logger.error("VITO API 키가 설정되지 않았습니다.")
            raise Exception("VITO API 키가 설정되지 않았습니다.")
        
        logger.info(f"VITO STT 시작 - 파일: {audio_file.name}, 크기: {audio_file.size} bytes")
        
        # 임시 파일로 오디오 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        try:
            # 1단계: 전사 작업 생성
            headers = {
                'Authorization': f'Bearer {api_key}',
            }
            
            # 파일 업로드를 위한 multipart form-data
            with open(temp_file_path, 'rb') as f:
                files = {
                    'file': (audio_file.name, f, audio_file.content_type)
                }
                
                data = {
                    'config': json.dumps({
                        'use_itn': True,  # Inverse Text Normalization
                        'use_disfluency_filter': True,  # 비유창성 필터
                        'use_profanity_filter': False,  # 욕설 필터 (보이스피싱 탐지를 위해 비활성화)
                        'paragraph_splitter': {
                            'max': 50  # 문단 분할 최대 길이
                        }
                    })
                }
                
                # 전사 작업 생성 요청
                response = requests.post(
                    f'{settings.VITO_API_URL}/transcribe',
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 401:
                    # 토큰 만료 시 갱신 시도
                    logger.warning("VITO API 토큰 만료, 갱신 시도")
                    new_token = refresh_vito_token()
                    
                    if new_token:
                        # 새 토큰으로 다시 시도
                        headers['Authorization'] = f'Bearer {new_token}'
                        logger.info("새 토큰으로 VITO API 재시도")
                        
                        response = requests.post(
                            f'{settings.VITO_API_URL}/transcribe',
                            headers=headers,
                            files=files,
                            data=data,
                            timeout=30
                        )
                        
                        if response.status_code != 200:
                            error_detail = response.text[:200] if response.text else "응답 없음"
                            logger.error(f"VITO API 재시도 실패: {response.status_code} - {error_detail}")
                            raise Exception(f"VITO API 재시도 실패: HTTP {response.status_code}")
                    else:
                        logger.error("VITO 토큰 갱신 실패")
                        raise Exception("VITO API 인증 실패")
                        
                elif response.status_code != 200:
                    error_detail = response.text[:200] if response.text else "응답 없음"
                    logger.error(f"VITO API 요청 실패: {response.status_code} - {error_detail}")
                    raise Exception(f"VITO API 요청 실패: HTTP {response.status_code}")
                
                result = response.json()
                transcribe_id = result.get('id')
                
                if not transcribe_id:
                    logger.error(f"전사 작업 ID 없음: {result}")
                    raise Exception("전사 작업 생성 실패")
                
                logger.info(f"VITO 전사 작업 생성 성공: ID={transcribe_id}")
            
            # 2단계: 전사 결과 조회 (폴링)
            max_attempts = 30  # 최대 30번 시도 (약 30초)
            attempt = 0
            
            logger.info(f"VITO 전사 상태 폴링 시작 (최대 {max_attempts}초)")
            while attempt < max_attempts:
                time.sleep(1)  # 1초 대기
                attempt += 1
                
                # 전사 상태 확인
                status_response = requests.get(
                    f'{settings.VITO_API_URL}/transcribe/{transcribe_id}',
                    headers=headers,
                    timeout=10
                )
                
                if status_response.status_code != 200:
                    logger.error(f"전사 상태 확인 실패: {status_response.status_code}")
                    raise Exception("전사 상태 확인 실패")
                
                status_result = status_response.json()
                status = status_result.get('status')
                
                logger.debug(f"VITO 전사 상태 확인 ({attempt}/{max_attempts}): {status}")
                
                if status == 'completed':
                    # 전사 완료 - 결과 추출
                    utterances = status_result.get('results', {}).get('utterances', [])
                    transcript_parts = []
                    
                    for utterance in utterances:
                        msg = utterance.get('msg', '')
                        if msg.strip():
                            transcript_parts.append(msg.strip())
                    
                    if transcript_parts:
                        transcript = ' '.join(transcript_parts)
                        logger.info(f"VITO STT 성공: {len(transcript)} 글자")
                        return transcript
                    else:
                        logger.warning("VITO STT 결과가 비어있음")
                        return "음성 인식 결과가 없습니다."
                
                elif status == 'failed':
                    error_msg = status_result.get('message', '알 수 없는 오류')
                    logger.error(f"VITO 전사 실패: {error_msg}")
                    raise Exception(f"VITO 전사 실패: {error_msg}")
                
                # 아직 처리 중인 경우 계속 대기
                if attempt % 5 == 0:  # 5초마다 상태 로그 출력
                    logger.info(f"VITO 전사 진행 중... ({attempt}/{max_attempts}초 경과)")
            
            # 시간 초과
            logger.error("VITO STT 처리 시간 초과")
            raise Exception("음성 인식 처리 시간이 초과되었습니다.")
            
        finally:
            # 임시 파일 삭제
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    except Exception as e:
        logger.error(f"VITO STT 오류: {str(e)}")
        # 백업으로 목업 데이터 반환 (개발 중에만 사용)
        mock_responses = [
            "안녕하세요. 저는 금융감독원에서 나온 김철수입니다. 고객님의 계좌에 이상 거래가 발견되어 연락드렸습니다.",
            "고객님께서 문의하신 상품에 대해 안내드리겠습니다.",
            "보안을 위해 계좌번호와 비밀번호를 확인해주시기 바랍니다.",
            "투자 상품 관련해서 수익률이 매우 좋은 상품이 있어 연락드렸습니다."
        ]
        logger.warning("VITO API 실패로 목업 데이터 사용")
        return f"[VITO API 오류 - 목업 사용] {random.choice(mock_responses)}"

def analyze_with_first_model(text):
    """1차 Stacking 모델 분석 - 보류 구간 로직 포함"""
    try:
        logger.info("1차 모델 분석 시작")
        
        # 1차 Pipeline 모델 로드 확인
        if not stacking_model:
            load_models()
        
        if not stacking_model:
            logger.error("1차 Pipeline 모델이 로드되지 않음")
            # 키워드 기반 폴백만 사용 (실제 모델 없을 때만)
            return analyze_with_keyword_fallback(text)
        
        # 텍스트 전처리 (노트북과 동일한 방식)
        processed_text = tokenize_and_filter(text)
        
        if not processed_text.strip():
            logger.warning("전처리된 텍스트가 비어있음")
            processed_text = text
        
        logger.info(f"전처리 완료: 원본 길이={len(text)}, 처리 후 길이={len(processed_text)}")
        
        # 1차 Pipeline 모델에 키위 토큰화된 텍스트 직접 입력
        logger.info(f"Pipeline 모델 타입: {type(stacking_model).__name__}")
        logger.info(f"입력 텍스트 (처음 100자): {processed_text[:100]}...")
        
        # Pipeline 모델 예측 수행 (내부에서 TF-IDF 벡터화 → Stacking 수행)
        prediction = stacking_model.predict([processed_text])[0]
        probability = stacking_model.predict_proba([processed_text])[0]
        
        # 피싱일 확률 (클래스 1의 확률)
        phishing_probability = probability[1] if len(probability) > 1 else 0.5
        
        logger.info(f"1차 Pipeline 모델 예측: prediction={prediction}, phishing_prob={phishing_probability:.4f}")
        logger.info(f"전체 확률 분포: {probability}")
        
        # 보류 구간 판별 로직
        NORMAL_THRESHOLD = 0.3      # 0.3 이하: 일반통화
        PHISHING_THRESHOLD = 0.75   # 0.75 이상: 보이스피싱
        
        if phishing_probability <= NORMAL_THRESHOLD:
            # 일반통화로 즉시 판별
            final_prediction = 0
            decision_type = "immediate_normal"
            logger.info(f"즉시 일반통화 판별: 확률={phishing_probability:.3f} <= {NORMAL_THRESHOLD}")
            
        elif phishing_probability >= PHISHING_THRESHOLD:
            # 보이스피싱으로 즉시 판별
            final_prediction = 1
            decision_type = "immediate_phishing"
            logger.info(f"즉시 보이스피싱 판별: 확률={phishing_probability:.3f} >= {PHISHING_THRESHOLD}")
            
        else:
            # 보류 구간 - 2차 모델로 전달
            final_prediction = -1  # 보류 상태
            decision_type = "pending"
            logger.info(f"보류 구간 - 2차 모델 필요: {NORMAL_THRESHOLD} < {phishing_probability:.3f} < {PHISHING_THRESHOLD}")
        
        result = {
            'prediction': final_prediction,
            'confidence': float(phishing_probability),
            'probabilities': probability.tolist(),
            'decision_type': decision_type,
            'thresholds': {
                'normal': NORMAL_THRESHOLD,
                'phishing': PHISHING_THRESHOLD
            },
            'model_used': 'stacking_v2',
            'processed_text_length': len(processed_text)
        }
        
        logger.info(f"1차 모델 분석 완료: {result}")
        return result
        
    except Exception as e:
        logger.error(f"1차 모델 분석 실패: {str(e)}")
        
        # 실패 시 보류로 처리하여 2차 모델로 전달
        import random
        fallback_confidence = 0.5 + random.uniform(-0.1, 0.1)  # 0.4~0.6 범위의 랜덤값
        return {
            'prediction': -1,  # 보류 상태
            'confidence': fallback_confidence,
            'probabilities': [1-fallback_confidence, fallback_confidence],
            'decision_type': "error_fallback",
            'error': str(e),
            'model_used': 'stacking_v2_failed'
        }

def analyze_with_second_model(text):
    """2차 KoBERT PyTorch 모델 분석"""
    try:
        logger.info("2차 KoBERT 모델 분석 시작")
        
        # 모델 로드 확인
        if not pytorch_model or not kobert_tokenizer:
            load_models()
        
        if not pytorch_model or not kobert_tokenizer:
            logger.error("2차 KoBERT 모델 또는 토크나이저가 로드되지 않음")
            
            # 백업: 랜덤 값 (LightGBM 백업 제거)
            import random
            fallback_confidence = 0.65 + random.uniform(-0.05, 0.05)  # 0.6~0.7 범위의 랜덤값
            return {
                'prediction': 1,  # 보수적으로 피싱으로 판별
                'confidence': fallback_confidence,
                'decision_type': "fallback_conservative",
                'model_used': 'kobert_fallback',
                'error': '2차 모델 로드 실패'
            }
        
        # 대화 데이터 전처리 (노트북의 create_dialogue_input과 동일)
        dialogue_input = create_dialogue_input(text)
        
        if not dialogue_input.strip():
            logger.warning("2차 모델용 대화 입력이 비어있음")
            dialogue_input = text
        
        logger.info(f"2차 모델 대화 입력 생성 완료: 길이={len(dialogue_input)}")
        
        # 토크나이징
        encoding = kobert_tokenizer(
            dialogue_input,
            truncation=True,
            padding='max_length',
            max_length=128,
            return_tensors='pt'
        )
        
        # GPU/CPU 설정
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        input_ids = encoding['input_ids'].to(device)
        attention_mask = encoding['attention_mask'].to(device)
        
        # 모델 추론
        with torch.no_grad():
            logits = pytorch_model(input_ids, attention_mask)
            probabilities = F.softmax(logits, dim=-1)
            
            # 피싱 확률 (클래스 1)
            phishing_prob = probabilities[0][1].cpu().item()
            
        logger.info(f"2차 KoBERT 모델 원시 예측 확률: {phishing_prob:.4f}")
        
        # 임계값 0.5로 최종 판별
        SECOND_MODEL_THRESHOLD = 0.5
        final_prediction = 1 if phishing_prob >= SECOND_MODEL_THRESHOLD else 0
        
        logger.info(f"2차 모델 실제 예측 수행: final_prediction={final_prediction}, phishing_prob={phishing_prob:.4f}")
        
        decision_type = "second_model_phishing" if final_prediction == 1 else "second_model_normal"
        
        result = {
            'prediction': final_prediction,
            'confidence': float(phishing_prob),
            'decision_type': decision_type,
            'threshold': SECOND_MODEL_THRESHOLD,
            'model_used': 'kobert_pytorch',
            'dialogue_input_length': len(dialogue_input)
        }
        
        logger.info(f"2차 KoBERT 모델 분석 완료: 예측={final_prediction}, 확률={phishing_prob:.3f}")
        return result
        
    except Exception as e:
        logger.error(f"2차 모델 분석 실패: {str(e)}")
        
        # 백업: LightGBM 제거됨 (TF-IDF 없으므로 사용 불가)
        
        # 실패 시 보수적으로 피싱으로 판별
        import random
        error_confidence = 0.7 + random.uniform(-0.1, 0.1)  # 0.6~0.8 범위의 랜덤값
        return {
            'prediction': 1,
            'confidence': error_confidence,
            'decision_type': "error_conservative",
            'model_used': 'kobert_failed',
            'error': str(e)
        }

def create_dialogue_input(text):
    """대화 텍스트를 모델 입력 형태로 변환 (노트북과 동일)"""
    try:
        # 기본적인 전처리만 수행
        dialogue_input = text.strip()
        
        # 너무 긴 텍스트는 처음 500자만 사용
        if len(dialogue_input) > 500:
            dialogue_input = dialogue_input[:500]
        
        # 빈 텍스트 처리
        if not dialogue_input:
            dialogue_input = "대화 내용이 없습니다."
        
        return dialogue_input
        
    except Exception as e:
        logger.error(f"대화 입력 생성 실패: {e}")
        return text  # 원본 텍스트 반환

def analyze_with_keyword_fallback(text):
    """1차 모델 로드 실패 시 키워드 기반 분석"""
    try:
        logger.warning("1차 Pipeline 모델 로드 실패 - 키워드 기반 분석 사용")
        
        # 텍스트 기반 간단한 키워드 탐지
        phishing_keywords = [
            '경찰', '검찰', '수사', '사이버', '금융감독원', '국정원',
            '계좌', '이체', '출금', '입금', '카드번호', '비밀번호',
            '개인정보', '주민번호', '본인확인', '인증번호',
            '긴급', '즉시', '지금', '바로', '당장'
        ]
        
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in phishing_keywords if keyword in text_lower)
        detected_keywords = [keyword for keyword in phishing_keywords if keyword in text_lower]
        
        logger.info(f"감지된 키워드: {detected_keywords}")
        
        # 키워드 기반 확률 계산
        import random
        if keyword_count >= 3:
            # 키워드가 많으면 피싱 확률 높음
            phishing_probability = 0.75 + random.uniform(-0.05, 0.1)  # 0.7~0.85
        elif keyword_count >= 1:
            # 키워드가 적으면 보류 구간
            phishing_probability = 0.5 + random.uniform(-0.1, 0.1)   # 0.4~0.6
        else:
            # 키워드가 없으면 정상 확률 높음
            phishing_probability = 0.25 + random.uniform(-0.05, 0.1)  # 0.2~0.35
        
        logger.info(f"키워드 기반 분석: {keyword_count}개 키워드, 피싱 확률={phishing_probability:.4f}")
        
        # 보류 구간 판별 로직
        NORMAL_THRESHOLD = 0.3
        PHISHING_THRESHOLD = 0.75
        
        if phishing_probability <= NORMAL_THRESHOLD:
            final_prediction = 0
            decision_type = "keyword_immediate_normal"
        elif phishing_probability >= PHISHING_THRESHOLD:
            final_prediction = 1
            decision_type = "keyword_immediate_phishing"
        else:
            final_prediction = -1  # 보류
            decision_type = "keyword_pending"
        
        result = {
            'prediction': final_prediction,
            'confidence': phishing_probability,
            'decision_type': decision_type,
            'model_used': 'keyword_fallback',
            'keywords_detected': keyword_count,
            'detected_keywords': detected_keywords
        }
        
        logger.info(f"키워드 기반 1차 분석 완료: 예측={final_prediction}, 확률={phishing_probability:.3f}")
        return result
        
    except Exception as e:
        logger.error(f"키워드 기반 분석 실패: {e}")
        import random
        return {
            'prediction': -1,
            'confidence': 0.5 + random.uniform(-0.1, 0.1),
            'decision_type': "fallback_error",
            'model_used': 'error_fallback',
            'error': str(e)
        }

def analyze_with_lgbm_fallback(text):
    """백업용 LightGBM 모델 분석 (더 이상 사용하지 않음)"""
    try:
        logger.info("백업 LightGBM 모델 분석 시작 (deprecated)")
        
        # LightGBM과 TF-IDF 모델 확인
        if not lgbm_model:
            logger.error("백업 LightGBM 모델이 없음")
            raise Exception("LightGBM 모델 없음")
        
        # ❌ TF-IDF가 별도로 로딩되지 않으므로 백업 모델 사용 불가
        logger.error("TF-IDF 벡터라이저가 별도로 로딩되지 않아 LightGBM 백업 모델 사용 불가")
        raise Exception("TF-IDF 벡터라이저 없음")
        
    except Exception as e:
        logger.error(f"백업 LightGBM 모델 분석 실패: {e}")
        
        # 최종 백업: 랜덤 값
        import random
        fallback_confidence = 0.65 + random.uniform(-0.05, 0.05)
        return {
            'prediction': 1,
            'confidence': fallback_confidence,
            'decision_type': "final_fallback",
            'model_used': 'final_fallback',
            'error': str(e)
        }

def generate_llm_explanation(text, first_result, second_result=None):
    """OpenAI GPT-4o를 사용한 보이스피싱 분석 설명 생성"""
    try:
        # 최종 판별 결과 결정
        if second_result is not None:
            # 2차 모델 결과 사용
            final_prediction = second_result['prediction']
            confidence = second_result['confidence']
            decision_source = "2차 모델 (LightGBM)"
        else:
            # 1차 모델 결과 사용
            final_prediction = first_result['prediction']
            confidence = first_result['confidence']
            decision_source = "1차 모델 (Stacking)"
        
        # OpenAI API 키 확인
        openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not openai_api_key or openai_api_key == 'your_openai_api_key_here':
            logger.warning("OpenAI API 키가 설정되지 않음. 기본 로직 사용")
            return generate_fallback_explanation(text, first_result, second_result)
        
        # OpenAI API 호출
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)
        
        # 프롬프트 생성
        is_phishing = final_prediction == 1
        prompt = create_analysis_prompt(text, is_phishing, confidence, decision_source, first_result, second_result)
        
        # GPT-4o 호출
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 보이스피싱 전문 분석가입니다. 주어진 통화 내용과 AI 모델의 분석 결과를 바탕으로 사용자에게 명확하고 실용적인 경고 메시지와 설명을 제공해야 합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3,
            timeout=10
        )
        
        llm_response = response.choices[0].message.content.strip()
        
        # LLM 응답 파싱
        parsed_result = parse_llm_response(llm_response, final_prediction, confidence, decision_source, first_result)
        
        logger.info(f"OpenAI LLM 설명 생성 완료: {parsed_result['phishing_type']}")
        return parsed_result
        
    except Exception as e:
        logger.error(f"OpenAI LLM 설명 생성 실패: {str(e)}")
        # 실패 시 기본 로직으로 폴백
        return generate_fallback_explanation(text, first_result, second_result)

def create_analysis_prompt(text, is_phishing, confidence, decision_source, first_result, second_result=None):
    """OpenAI 프롬프트 생성"""
    
    base_prompt = f"""
다음은 보이스피싱 탐지 시스템의 분석 결과입니다:

**통화 내용 (STT 변환):**
{text[:500]}{"..." if len(text) > 500 else ""}

**AI 모델 분석 결과:**
- 최종 판별: {"보이스피싱" if is_phishing else "정상 통화"}
- 신뢰도: {confidence:.1%}
- 판별 모델: {decision_source}
- 1차 모델 결과: {first_result.get('decision_type', 'N/A')}
"""

    if second_result:
        base_prompt += f"- 2차 모델 결과: {second_result.get('decision_type', 'N/A')}\n"

    task_prompt = """
위 정보를 바탕으로 다음 형식으로 응답해주세요:

PHISHING_TYPE: [구체적인 피싱 유형 또는 '정상통화']
WARNING: [사용자를 위한 명확한 경고 메시지 또는 안전 메시지]
EXPLANATION: [왜 이런 판별을 했는지에 대한 간단한 설명]
RISK_FACTORS: [위험 요소들을 쉼표로 구분, 없으면 '없음']

**보이스피싱 유형 분류 기준:**
- 기관사칭형: 공공기관(국세청, 경찰청, 금감원 등)을 사칭
- 가족지인사칭형: 가족, 친구, 지인을 사칭하여 돈을 요구
- 대출빙자형: 대출 제안으로 개인정보나 수수료 요구
- 투자빙자형: 고수익 투자를 미끼로 돈을 요구
- 수사기관사칭형: 검찰, 경찰 등 수사기관을 사칭
- 금융기관사칭형: 은행, 카드사 등 금융기관을 사칭
- 택배사칭형: 택배회사를 사칭하여 개인정보 요구
- 세금환급형: 세금환급, 환급금 수령 등 명목으로 개인정보, 계좌 요구
- 콜백스미싱형: 결제 취소, 쇼핑몰 주문 등 문자로 유도 후 연결, 악성앱 설치 유도

**중요 지침:**
1. 경고 메시지는 구체적이고 실행 가능한 조치를 포함해야 합니다
2. 보이스피싱의 경우 즉시 통화 종료, 직접 기관 확인 등을 권고
3. 정상 통화도 지속적인 주의를 당부
4. 한국어로 자연스럽게 작성
5. 각 항목은 한 줄로 작성
"""
    
    return base_prompt + task_prompt

def parse_llm_response(llm_response, final_prediction, confidence, decision_source, first_result):
    """LLM 응답 파싱"""
    try:
        lines = llm_response.strip().split('\n')
        result = {
            'phishing_type': '분석 오류',
            'warning': '분석 결과를 처리하는 중 오류가 발생했습니다.',
            'explanation': 'LLM 응답 파싱에 실패했습니다.',
            'risk_factors': [],
            'analysis_process': [],
            'confidence_level': confidence,
            'decision_source': decision_source
        }
        
        for line in lines:
            if line.startswith('PHISHING_TYPE:'):
                result['phishing_type'] = line.replace('PHISHING_TYPE:', '').strip()
            elif line.startswith('WARNING:'):
                result['warning'] = line.replace('WARNING:', '').strip()
            elif line.startswith('EXPLANATION:'):
                result['explanation'] = line.replace('EXPLANATION:', '').strip()
            elif line.startswith('RISK_FACTORS:'):
                factors_str = line.replace('RISK_FACTORS:', '').strip()
                if factors_str and factors_str != '없음':
                    result['risk_factors'] = [f.strip() for f in factors_str.split(',')]
                else:
                    result['risk_factors'] = []
        
        # 분석 과정 정보 추가
        process_info = []
        if first_result.get('decision_type') == 'immediate_normal':
            process_info.append("1차 모델에서 즉시 정상 판별")
        elif first_result.get('decision_type') == 'immediate_phishing':
            process_info.append("1차 모델에서 즉시 피싱 판별")
        elif first_result.get('decision_type') == 'pending':
            process_info.append("1차 모델 보류 → 2차 모델 분석")
        
        result['analysis_process'] = process_info
        return result
        
    except Exception as e:
        logger.error(f"LLM 응답 파싱 오류: {str(e)}")
        return generate_fallback_explanation("", {'prediction': final_prediction, 'confidence': confidence}, None)

def generate_fallback_explanation(text, first_result, second_result=None):
    """OpenAI 실패 시 사용할 기본 설명 생성 (기존 로직)"""
    try:
        # 최종 판별 결과 결정
        if second_result is not None:
            final_prediction = second_result['prediction']
            confidence = second_result['confidence']
            decision_source = "2차 모델 (LightGBM)"
        else:
            final_prediction = first_result['prediction']
            confidence = first_result['confidence']
            decision_source = "1차 모델 (Stacking)"
        
        # 피싱 유형별 메시지 템플릿 (한국 보이스피싱 실제 유형 반영)
        phishing_types = ['기관사칭형', '지인사칭형', '택배사칭형', '대출빙자형', '투자빙자형', '수사기관사칭형', '금융기관사칭형']
        
        if final_prediction == 1:  # 보이스피싱
            phishing_type = random.choice(phishing_types)
            
            if confidence >= 0.8:
                warning = f"⚠️ 고위험: 보이스피싱 가능성이 매우 높습니다 (신뢰도: {confidence:.1%}). 즉시 통화를 종료하고 해당 기관에 직접 확인하시기 바랍니다."
            elif confidence >= 0.6:
                warning = f"⚠️ 중위험: 보이스피싱 가능성이 높습니다 (신뢰도: {confidence:.1%}). 통화 내용을 신중히 검토하고 의심스러우면 통화를 종료하세요."
            else:
                warning = f"⚠️ 저위험: 보이스피싱 가능성이 있습니다 (신뢰도: {confidence:.1%}). 개인정보 제공에 주의하시기 바랍니다."
            
            explanation = f"{decision_source}에서 '{phishing_type}' 패턴으로 분류되었습니다. 기관명 사칭, 개인정보 요구, 금전 관련 유도 등의 의심 요소가 감지되었습니다."
            risk_factors = ["기관명 언급", "계좌번호 요구", "개인정보 확인 요청", "금전 관련 언급"]
            
        else:  # 정상통화
            phishing_type = '정상통화'
            
            if confidence >= 0.8:
                warning = f"✅ 안전: 정상적인 통화로 판단됩니다 (신뢰도: {confidence:.1%})."
            elif confidence >= 0.6:
                warning = f"✅ 대체로 안전: 정상 통화 가능성이 높습니다 (신뢰도: {confidence:.1%}). 하지만 항상 주의하시기 바랍니다."
            else:
                warning = f"⚠️ 주의: 판별이 애매한 통화입니다 (신뢰도: {confidence:.1%}). 지속적인 주의가 필요합니다."
            
            explanation = f"{decision_source}에서 정상 통화로 분류되었습니다. 보이스피싱 의심 요소가 발견되지 않았거나 미미한 수준입니다."
            risk_factors = []
        
        # 분석 과정 정보 추가
        process_info = []
        if first_result.get('decision_type') == 'immediate_normal':
            process_info.append("1차 모델에서 즉시 정상 판별")
        elif first_result.get('decision_type') == 'immediate_phishing':
            process_info.append("1차 모델에서 즉시 피싱 판별")
        elif first_result.get('decision_type') == 'pending':
            process_info.append("1차 모델 보류 → 2차 모델 분석")
        
        return {
            'phishing_type': phishing_type,
            'warning': warning,
            'explanation': explanation,
            'risk_factors': risk_factors,
            'analysis_process': process_info,
            'confidence_level': confidence,
            'decision_source': decision_source,
            'note': '※ 기본 분석 로직 사용 (OpenAI API 연결 실패)'
        }
        
    except Exception as e:
        logger.error(f"기본 설명 생성 실패: {str(e)}")
        return {
            'phishing_type': '분석 오류',
            'warning': "분석 중 오류가 발생했습니다. 통화 내용을 수동으로 검토해주세요.",
            'explanation': "시스템 오류로 인해 정확한 분석을 수행하지 못했습니다.",
            'risk_factors': [],
            'analysis_process': ['분석 오류 발생'],
            'confidence_level': 0.5,
            'decision_source': '오류',
            'error': str(e)
        }


def safe_truncate_field(value, max_length, field_name="field"):
    """데이터베이스 필드 길이 제한에 맞춰 안전하게 자르기"""
    if not value:
        return value
    
    str_value = str(value)
    if len(str_value) > max_length:
        truncated_value = str_value[:max_length]
        logger.warning(f"{field_name} 필드 길이 제한으로 자름: {len(str_value)} -> {max_length} (원본: {str_value[:100]}...)")
        return truncated_value
    return str_value

def generate_short_id():
    """데이터베이스 제약에 안전한 짧은 고유 ID 생성"""
    import time
    import random
    
    # 현재 시간(밀리초) + 랜덤 숫자로 고유성 보장하면서 길이 단축
    timestamp = str(int(time.time() * 1000))[-10:]  # 뒤 10자리만 사용
    random_part = str(random.randint(10000, 99999))  # 5자리 랜덤
    return f"{timestamp}{random_part}"  # 총 15자

def safe_file_id(ocrn_no):
    """file_id 필드 길이 제한에 맞춘 안전한 ID 생성"""
    if not ocrn_no:
        return generate_short_id()
    
    str_ocrn_no = str(ocrn_no)
    
    # 데이터베이스 제약에 따른 단계별 처리
    if len(str_ocrn_no) <= 20:
        # 20자 이하면 그대로 사용
        return str_ocrn_no
    elif len(str_ocrn_no) <= 50:
        # 21-50자면 migration 적용 후 사용 가능
        logger.info(f"file_id 길이 {len(str_ocrn_no)}자 - migration 필요")
        return str_ocrn_no
    else:
        # 50자 초과면 앞부분만 사용
        logger.warning(f"file_id 길이 {len(str_ocrn_no)}자 초과 - 50자로 단축")
        return str_ocrn_no[:50]


def log_system_info(level, message, file_name=None, ip_address=None):
    """시스템 로그를 데이터베이스에 기록하는 헬퍼 함수"""
    try:
        log_entry = SystemLog.objects.create(
            level=level,
            message=message,
            file_name=file_name or 'SYSTEM',
            ip_address=ip_address,
            created_at=timezone.now()
        )
        logger.info(f"[DB_LOG] 성공 저장 ID={log_entry.id}, {level}: {message}")
        return log_entry
    except Exception as e:
        logger.error(f"시스템 로그 저장 실패: {e}")
        logger.error(f"저장 시도 데이터: level={level}, message={message[:100]}, file_name={file_name}, ip={ip_address}")
        # 스택 트레이스도 로그에 출력
        import traceback
        logger.error(f"스택 트레이스: {traceback.format_exc()}")
        return None

@csrf_exempt
@require_http_methods(["POST"])
def log_frontend_event(request):
    """프론트엔드에서 전송된 로그 이벤트를 처리"""
    try:
        data = json.loads(request.body)
        client_ip = get_client_ip(request)
        
        # 프론트엔드 로그를 시스템 로그에 기록
        log_entry = log_system_info(
            level=data.get('level', 'INFO'),
            message=f"[FRONTEND] {data.get('message', '')}",
            file_name=data.get('file_name', 'FRONTEND'),
            ip_address=client_ip
        )
        
        if log_entry:
            return JsonResponse({
                'success': True,
                'log_id': log_entry.id,
                'message': '프론트엔드 로그가 성공적으로 기록되었습니다.'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': '로그 기록에 실패했습니다.'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '잘못된 JSON 형식입니다.'
        }, status=400)
    except Exception as e:
        logger.error(f"프론트엔드 로그 처리 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': '서버 내부 오류가 발생했습니다.'
        }, status=500)

def get_client_ip(request):
    """클라이언트 IP 주소 가져오기"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def index(request):
    """메인 페이지 렌더링"""
    return render(request, 'voice_phishing/index.html')

def analysis(request):
    """분석 진행 페이지 뷰"""
    return render(request, 'voice_phishing/analysis.html')

def result(request):
    """분석 결과 페이지 뷰"""
    return render(request, 'voice_phishing/result.html')


@csrf_exempt
@require_http_methods(["POST"])
def analyze(request):
    """음성 파일 분석 API"""
    start_time = time.time()
    client_ip = get_client_ip(request)
    # 프론트엔드에서 전달한 task_id가 있으면 이를 사용하고, 없으면 새로 생성
    task_id = request.POST.get('task_id')
    ocrn_no = task_id if task_id else str(uuid.uuid4())  # 고유 발생번호
    
    # 분석 시작 로그 (기본 정보 확인용)
    logger.info(f"=== 분석 요청 시작 ===")
    logger.info(f"클라이언트 IP: {client_ip}")
    logger.info(f"발생번호 (ocrn_no): {ocrn_no} (길이: {len(ocrn_no)})")
    logger.info(f"요청 메서드: {request.method}")
    logger.info(f"콘텐츠 타입: {request.content_type}")
    
    # 데이터베이스 로그 저장 테스트
    try:
        start_log = log_system_info("INFO", "분석 요청 시작", "ANALYSIS_START", client_ip)
        if start_log:
            logger.info(f"시작 로그 저장 성공: ID={start_log.id}")
        else:
            logger.error("시작 로그 저장 실패")
    except Exception as e:
        logger.error(f"시작 로그 저장 중 예외: {str(e)}")
    
    try:
        # 업로드된 파일 확인
        if 'audio_file' not in request.FILES:
            # 기존 SystemLog 사용 (VoicePhishingSystemLog 대신)
            SystemLog.objects.create(
                level='ERROR',
                message='오디오 파일이 업로드되지 않음',
                file_name='UPLOAD_VALIDATION',
                ip_address=client_ip
            )
            return JsonResponse({
                'success': False,
                'error': '오디오 파일이 필요합니다.'
            }, status=400)
        
        audio_file = request.FILES['audio_file']
        
        # 파일 형식 검증
        allowed_extensions = ['.mp3', '.wav', '.amr', '.m4a']
        file_extension = '.' + audio_file.name.lower().split('.')[-1]
        
        if file_extension not in allowed_extensions:
            SystemLog.objects.create(
                level='ERROR',
                message=f'지원하지 않는 파일 형식: {file_extension}',
                file_name=audio_file.name,
                ip_address=client_ip
            )
            return JsonResponse({
                'success': False,
                'error': f'지원하지 않는 파일 형식입니다. 지원 형식: {", ".join(allowed_extensions)}'
            }, status=400)
        
        # 파일 크기 검증 (50MB 제한)
        max_size = 50 * 1024 * 1024  # 50MB
        if audio_file.size > max_size:
            SystemLog.objects.create(
                level='ERROR',
                message=f'파일 크기 초과: {audio_file.size} bytes (최대: {max_size} bytes)',
                file_name=audio_file.name,
                ip_address=client_ip
            )
            return JsonResponse({
                'success': False,
                'error': '파일 크기가 너무 큽니다. 최대 50MB까지 지원합니다.'
            }, status=400)
        
        # 1단계: 오디오 파일 저장
        print_separator()
        log_and_print("INFO", "[FILE UPLOAD] File Upload Stage Started")
        log_and_print("INFO", f"   Request ID: {ocrn_no}")
        log_and_print("INFO", f"   File Name: {audio_file.name}")
        log_and_print("INFO", f"   File Size: {audio_file.size:,} bytes ({audio_file.size/1024/1024:.2f} MB)")
        log_and_print("INFO", f"   File Type: {file_extension}")
        log_and_print("INFO", f"   Client IP: {client_ip}")
        
        upload_dir = BASE_DIR / 'media' / 'uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        saved_file_path = upload_dir / f"{ocrn_no}_{audio_file.name}"
        
        log_and_print("INFO", "[FILE SAVE] File Saving Started...")
        log_and_print("INFO", f"   Save Path: {saved_file_path}")
        
        with open(saved_file_path, 'wb') as f:
            for chunk in audio_file.chunks():
                f.write(chunk)
        
        log_and_print("INFO", f"[SUCCESS] File Save Complete: {saved_file_path}")
        log_and_print("INFO", f"   Saved File Size: {saved_file_path.stat().st_size:,} bytes")
        
        # 2단계: STT 처리 (진행률 업데이트)
        print_separator()
        log_and_print("INFO", "[STT] STT Conversion Stage Started")
        log_and_print("INFO", f"   Request ID: {ocrn_no}")
        log_and_print("INFO", f"   Using VITO API")
        log_and_print("INFO", f"   File: {audio_file.name}")
        
        send_progress_update(ocrn_no, 0, 0, "VITO STT로 음성을 텍스트로 변환하고 있습니다...", "STT 변환")
        try:
            log_system_info("INFO", f"VITO STT 시작: {audio_file.name}", audio_file.name, client_ip)
            
            log_and_print("INFO", "[VITO] Calling VITO API...")
            start_time = time.time()
            transcript = vito_stt(audio_file)
            end_time = time.time()
            
            log_and_print("INFO", "[SUCCESS] VITO STT Conversion Complete!")
            log_and_print("INFO", f"   Processing Time: {end_time - start_time:.2f} seconds")
            log_and_print("INFO", f"   Converted Text Length: {len(transcript):,} characters")
            log_and_print("INFO", f"   Text Preview (first 200 chars): {transcript[:200]}...")
            
            # STT 품질 검증
            if len(transcript.strip()) < 10:
                log_and_print("WARNING", "[WARNING] STT result too short (less than 10 characters)")
            elif "[VITO API 오류" in transcript:
                log_and_print("WARNING", "[WARNING] Using mock data due to STT API error")
            else:
                log_and_print("INFO", "[SUCCESS] STT quality validation passed")
                
            log_system_info("INFO", f"VITO STT 완료: {len(transcript)} 글자", audio_file.name, client_ip)
            send_progress_update(ocrn_no, 0, 100, "STT 변환이 완료되었습니다.", "STT 변환")
        except Exception as e:
            SystemLog.objects.create(
                level='ERROR',
                message=f'STT 처리 실패: {str(e)}',
                file_name=audio_file.name,
                ip_address=client_ip
            )
            logger.error(f"VITO STT 실패: {str(e)}")
            transcript = "STT 처리에 실패했습니다."
            send_analysis_error(ocrn_no, f"STT 처리 실패: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'STT 처리에 실패했습니다.'
            }, status=500)
        
        # 3단계: 텍스트 전처리
        print_separator()
        log_and_print("INFO", "[PREPROCESS] Text Preprocessing Stage Started")
        log_and_print("INFO", f"   Original Text Length: {len(transcript):,} characters")
        
        prcs_cont_1 = preprocess_text(transcript)
        prcs_cont_2 = {"processed_text": transcript}  # 2차 전처리는 임시
        
        log_and_print("INFO", "[SUCCESS] Text Preprocessing Complete")
        log_and_print("INFO", f"   1st Processing Result: {len(str(prcs_cont_1)):,} characters")
        log_and_print("INFO", f"   2nd Processing Result: {len(str(prcs_cont_2)):,} characters")
        
        # 4단계: 파일 정보 저장 (파일명 길이 제한 처리)
        print_separator()
        log_and_print("INFO", "[DATABASE] Database Save Stage Started")
        log_and_print("INFO", "   Inserting data into ProcessdFile table")
        
        file_name = audio_file.name
        if len(file_name) > 295:  # 300자 제한에서 여유분 5자
            file_name = file_name[:295] + "..."
            log_and_print("WARNING", f"[WARNING] Filename truncated: {len(audio_file.name)} -> {len(file_name)} chars")
        
        log_and_print("INFO", "[DB CREATE] Creating database record...")
        log_and_print("INFO", f"   ocrn_no: {ocrn_no}")
        log_and_print("INFO", f"   trsc_file_nm: {file_name}")
        log_and_print("INFO", f"   transcript length: {len(transcript):,} chars")
        log_and_print("INFO", f"   vldtn_yn: Y")
        log_and_print("INFO", f"   file_path: {str(saved_file_path.relative_to(BASE_DIR))}")
        
        processed_file = ProcessdFile.objects.create(
            ocrn_no=ocrn_no,
            ocrn_hm=timezone.now(),
            trsc_file_nm=file_name,
            transcript=transcript,
            prcs_cont_1=prcs_cont_1,
            prcs_cont_2=prcs_cont_2,
            vldtn_yn='Y',
            stats_file_path=f'/stats/{ocrn_no}.json',
            file_path=str(saved_file_path.relative_to(BASE_DIR))
        )
        
        log_and_print("INFO", "[SUCCESS] ProcessdFile Record Created")
        log_and_print("INFO", f"   Generated Record ID: {processed_file.id}")
        
        # 5단계: 1차 모델 분석 (진행률 업데이트)
        print_separator()
        log_and_print("INFO", "[ML ANALYSIS] 1st ML Model Analysis Stage Started")
        log_and_print("INFO", f"   Model Type: Stacking (LightGBM + SVM + Logistic)")
        log_and_print("INFO", f"   Input Text Length: {len(transcript):,} characters")
        log_and_print("INFO", f"   Request ID: {ocrn_no}")
        
        send_progress_update(ocrn_no, 1, 0, "1차 ML 모델로 보이스피싱 패턴을 분석하고 있습니다...", "1차 ML 분석")
        log_system_info("INFO", "1차 모델 분석 시작", audio_file.name, client_ip)
        
        start_time = time.time()
        first_model_result = analyze_with_first_model(transcript)
        end_time = time.time()
        
        # 결과 해석
        prediction = first_model_result.get('prediction', 0)
        confidence = first_model_result.get('confidence', 0)
        
        prediction_text = {
            0: "Normal Call",
            1: "Voice Phishing",
            -1: "Hold (2nd Analysis Required)"
        }.get(prediction, "Unknown")
        
        log_and_print("INFO", "[SUCCESS] 1st ML Model Analysis Complete!")
        log_and_print("INFO", f"   Processing Time: {end_time - start_time:.3f} seconds")
        log_and_print("INFO", f"   Prediction Result: {prediction} ({prediction_text})")
        log_and_print("INFO", f"   Confidence: {confidence:.4f} ({confidence*100:.2f}%)")
        log_and_print("INFO", f"   Model Response: {first_model_result}")
        
        log_system_info("INFO", f"1차 모델 분석 완료: 예측={first_model_result.get('prediction')}, 신뢰도={first_model_result.get('confidence', 0):.3f}", audio_file.name, client_ip)
        send_progress_update(ocrn_no, 1, 100, "1차 ML 분석이 완료되었습니다.", "1차 ML 분석")
        
        # 6단계: 2차 모델 분석 (조건부 실행)
        print_separator()
        log_and_print("INFO", "[DL ANALYSIS] 2nd DL Model Analysis Stage")
        
        second_model_result = None
        final_prediction = first_model_result['prediction']
        final_confidence = first_model_result['confidence']
        dl_jdgm_yn = 'N'  # 딥러닝 판단 여부
        
        if first_model_result['prediction'] == -1:  # 보류 구간
            log_and_print("INFO", "[DL START] Hold zone detected - Starting 2nd DL model analysis")
            log_and_print("INFO", f"   Model Type: KoBERT + LSTM")
            log_and_print("INFO", f"   1st Model Confidence: {first_model_result['confidence']:.4f}")
            log_and_print("INFO", f"   Detailed analysis required")
            
            send_progress_update(ocrn_no, 2, 0, "2차 DL 모델로 정밀 검증을 진행하고 있습니다...", "2차 DL 분석")
            log_system_info("INFO", "보류 구간 - 2차 모델 분석 시작", audio_file.name, client_ip)
            
            start_time = time.time()
            second_model_result = analyze_with_second_model(transcript)
            end_time = time.time()
            
            # 2차 모델 결과 해석
            dl_prediction = second_model_result.get('prediction', 0)
            dl_confidence = second_model_result.get('confidence', 0)
            
            dl_prediction_text = {
                0: "Normal Call",
                1: "Voice Phishing"
            }.get(dl_prediction, "Unknown")
            
            log_and_print("INFO", f"[SUCCESS] 2nd DL Model Analysis Complete!")
            log_and_print("INFO", f"   Processing Time: {end_time - start_time:.3f} seconds")
            log_and_print("INFO", f"   Prediction Result: {dl_prediction} ({dl_prediction_text})")
            log_and_print("INFO", f"   Confidence: {dl_confidence:.4f} ({dl_confidence*100:.2f}%)")
            log_and_print("INFO", f"   Model Response: {second_model_result}")
            
            log_system_info("INFO", f"2차 모델 분석 완료: 예측={second_model_result.get('prediction')}, 신뢰도={second_model_result.get('confidence', 0):.3f}", audio_file.name, client_ip)
            send_progress_update(ocrn_no, 2, 100, "2차 DL 분석이 완료되었습니다.", "2차 DL 분석")
            
            # 2차 모델 결과를 최종 결과로 사용
            final_prediction = second_model_result['prediction']
            final_confidence = second_model_result['confidence']
            dl_jdgm_yn = 'Y'
            
            log_and_print("INFO", f"[DECISION] Final Decision: Adopting 2nd model result")
        else:
            log_and_print("INFO", "[DECISION] Immediate classification by 1st model")
            log_and_print("INFO", f"   Classification Type: {first_model_result.get('decision_type', 'Unknown')}")
            log_and_print("INFO", f"   Skipping 2nd model analysis")
            
            log_system_info("INFO", f"1차 모델에서 즉시 판별: {first_model_result.get('decision_type', 'Unknown')}", audio_file.name, client_ip)
            
            log_and_print("INFO", f"[DECISION] Final Decision: Adopting 1st model result")
        
        # 최종 결과 요약
        final_prediction_text = {
            0: "Normal Call",
            1: "Voice Phishing"
        }.get(final_prediction, "Unknown")
        
        log_and_print("INFO", f"[SUMMARY] Final Analysis Result Summary")
        log_and_print("INFO", f"   Final Prediction: {final_prediction} ({final_prediction_text})")
        log_and_print("INFO", f"   Final Confidence: {final_confidence:.4f} ({final_confidence*100:.2f}%)")
        log_and_print("INFO", f"   DL Model Used: {'Yes' if dl_jdgm_yn == 'Y' else 'No'}")
        
        # 7단계: LLM 설명 생성 (진행률 업데이트)
        logger.info("="*80)
        print_separator()
        log_and_print("INFO", "[LLM] LLM Message Generation Stage Started")
        logger.info(f"   ├─ LLM 모델: GPT-4")
        logger.info(f"   ├─ 최종 예측: {final_prediction} ({final_prediction_text})")
        logger.info(f"   ├─ 최종 신뢰도: {final_confidence:.4f}")
        logger.info(f"   └─ 맞춤형 경고 메시지 생성")
        
        send_progress_update(ocrn_no, 3, 0, "GPT-4가 맞춤형 경고 메시지를 생성하고 있습니다...", "LLM 메시지 생성")
        log_system_info("INFO", "LLM 설명 생성 시작", audio_file.name, client_ip)
        
        start_time = time.time()
        llm_result = generate_llm_explanation(transcript, first_model_result, second_model_result)
        end_time = time.time()
        
        # LLM 결과 검증 및 로깅
        phishing_type = llm_result.get('phishing_type', 'Unknown')
        explanation = llm_result.get('explanation', '')
        prevention_tips = llm_result.get('prevention_tips', [])
        
        log_and_print("INFO", f"[SUCCESS] LLM Message Generation Complete!")
        logger.info(f"   ├─ 소요 시간: {end_time - start_time:.2f}초")
        logger.info(f"   ├─ 보이스피싱 유형: {phishing_type}")
        logger.info(f"   ├─ 설명 텍스트 길이: {len(explanation):,} 글자")
        logger.info(f"   ├─ 예방 팁 개수: {len(prevention_tips)}개")
        log_and_print("INFO", f"   Explanation Content (first 200 chars): {explanation[:200]}...")
        
        log_system_info("INFO", f"LLM 설명 생성 완료: 유형={llm_result.get('phishing_type', 'Unknown')}", audio_file.name, client_ip)
        send_progress_update(ocrn_no, 3, 100, "LLM 메시지 생성이 완료되었습니다.", "LLM 메시지 생성")
        
        # 8단계: ModelRegistry 등록
        logger.info("="*80)
        print_separator()
        log_and_print("INFO", "[DB REGISTRY] Database Integration Stage Started")
        logger.info("   └─ ModelRegistry 테이블 업데이트")
        
        # 1차 모델 등록
        log_and_print("INFO", "[MODEL REG] Registering 1st model...")
        first_model_registry, created = ModelRegistry.objects.get_or_create(
            mdl_id='STACKING_V2',
            defaults={
                'mdl_nm': 'Stacking Classifier V2 (1차 모델)',
                'use_yn': 'Y'
            }
        )
        if created:
            log_and_print("INFO", "[SUCCESS] 1st model newly registered in ModelRegistry")
            logger.info(f"   └─ 모델 ID: STACKING_V2")
        else:
            log_and_print("INFO", "[SUCCESS] 1st model confirmed in ModelRegistry (existing registration)")
        
        # 2차 모델 등록 (사용된 경우만)
        if dl_jdgm_yn == 'Y':
            log_and_print("INFO", "[MODEL REG] Registering 2nd model...")
            second_model_registry, created = ModelRegistry.objects.get_or_create(
                mdl_id='LGBM_V2',
                defaults={
                    'mdl_nm': 'LightGBM Model V2 (2차 모델)',
                    'use_yn': 'Y'
                }
            )
            if created:
                log_and_print("INFO", "[SUCCESS] 2nd model newly registered in ModelRegistry")
                logger.info(f"   └─ 모델 ID: LGBM_V2")
            else:
                log_and_print("INFO", "[SUCCESS] 2nd model confirmed in ModelRegistry (existing registration)")
        else:
            log_and_print("INFO", "[SKIP] Skipping 2nd model registration (not used)")
        
        # 9단계: 추론 결과 저장
        print_separator()
        log_and_print("INFO", "[INFERENCE] InferenceResult Table Save Started")
        
        rslt_id = str(uuid.uuid4())
        
        # 최종 결과를 문자열로 변환 (데이터베이스 저장용)
        ml_result_code = str(final_prediction) if final_prediction != -1 else '보류'
        
        log_and_print("INFO", f"[DATA PREP] Preparing data to save...")
        logger.info(f"   ├─ 결과 ID: {rslt_id}")
        logger.info(f"   ├─ 모델 ID: {'LGBM_V2' if dl_jdgm_yn == 'Y' else 'STACKING_V2'}")
        logger.info(f"   ├─ ML 결과 코드: {ml_result_code}")
        logger.info(f"   ├─ 예측 점수: {final_confidence:.4f}")
        logger.info(f"   ├─ DL 판단 여부: {dl_jdgm_yn}")
        log_and_print("INFO", f"   Voice Phishing Type: {llm_result['phishing_type']}")
        
        # 필드 길이 안전장치 적용
        safe_rslt_id = safe_truncate_field(rslt_id, 50, "rslt_id")
        safe_file_id_value = safe_file_id(ocrn_no)
        safe_mdl_id = safe_truncate_field('LGBM_V2' if dl_jdgm_yn == 'Y' else 'STACKING_V2', 20, "mdl_id")
        safe_ml_rslt_cd = safe_truncate_field(ml_result_code, 10, "ml_rslt_cd")
        safe_phsh_tp_nm = safe_truncate_field(llm_result['phishing_type'], 100, "phsh_tp_nm")
        
        log_and_print("INFO", f"[VALIDATION] Field Length Validation Complete")
        logger.info(f"   ├─ rslt_id: {len(safe_rslt_id)}/50 글자")
        logger.info(f"   ├─ file_id: {len(safe_file_id_value)}/20 글자")
        logger.info(f"   ├─ mdl_id: {len(safe_mdl_id)}/20 글자")
        logger.info(f"   ├─ ml_rslt_cd: {len(safe_ml_rslt_cd)}/10 글자")
        logger.info(f"   └─ phsh_tp_nm: {len(safe_phsh_tp_nm)}/100 글자")
        
        try:
            log_and_print("INFO", "[CREATE] Creating InferenceResult record...")
            inference_result = InferenceResult.objects.create(
                rslt_id=safe_rslt_id,
                ocrn_no=processed_file,
                mdl_id=safe_mdl_id,
                file_id=safe_file_id_value,
                prdt_scr=final_confidence,
                ml_rslt_cd=safe_ml_rslt_cd,
                dl_jdgm_yn=dl_jdgm_yn,
                phsh_tp_nm=safe_phsh_tp_nm,
                warn_cn=llm_result['warning'],  # TextField이므로 길이 제한 없음
                prdt_dt=timezone.now()
            )
            log_and_print("INFO", f"[SUCCESS] InferenceResult Save Complete!")
            logger.info(f"   ├─ 레코드 ID: {inference_result.id}")
            logger.info(f"   └─ 결과 ID: {safe_rslt_id}")
        except Exception as db_error:
            logger.error(f"InferenceResult 저장 실패: {str(db_error)}")
            logger.error(f"저장 시도 데이터: rslt_id={safe_rslt_id}, file_id={safe_file_id_value}")
            
            # 데이터 길이 문제일 경우 추가 단축 시도
            if "Data too long" in str(db_error) or "1406" in str(db_error):
                logger.warning("데이터 길이 문제로 인한 재시도 - 모든 필드를 더 짧게 단축")
                
                # 긴급 모드: 모든 필드를 최소 길이로 단축
                emergency_rslt_id = generate_short_id()
                emergency_file_id = generate_short_id()
                emergency_mdl_id = safe_mdl_id[:10] if safe_mdl_id else "UNKNOWN"
                
                try:
                    inference_result = InferenceResult.objects.create(
                        rslt_id=emergency_rslt_id,
                        ocrn_no=processed_file,
                        mdl_id=emergency_mdl_id,
                        file_id=emergency_file_id,
                        prdt_scr=final_confidence,
                        ml_rslt_cd=safe_ml_rslt_cd[:5] if safe_ml_rslt_cd else "ERROR",
                        dl_jdgm_yn=dl_jdgm_yn,
                        phsh_tp_nm=safe_phsh_tp_nm[:50] if safe_phsh_tp_nm else "분석오류",
                        warn_cn=llm_result['warning'][:500] if llm_result.get('warning') else "긴급모드저장",
                        prdt_dt=timezone.now()
                    )
                    logger.warning(f"긴급모드로 InferenceResult 저장 성공: {emergency_rslt_id}")
                    # 긴급모드에서 저장된 ID로 업데이트
                    safe_rslt_id = emergency_rslt_id
                except Exception as emergency_error:
                    logger.error(f"긴급모드 저장도 실패: {str(emergency_error)}")
                    raise Exception(f"데이터베이스 저장 완전 실패: {str(emergency_error)}")
            else:
                raise Exception(f"추론 결과 저장 실패: {str(db_error)}")
        
        # 10단계: 기존 모델과 호환성을 위한 저장
        logger.info("="*80)
        print_separator()
        log_and_print("INFO", "[ANALYSIS] AnalysisResult Table Save Started")
        
        is_phishing = final_prediction == 1
        total_processing_time = time.time() - start_time
        
        log_and_print("INFO", f"[DATA PREP] Preparing AnalysisResult data...")
        logger.info(f"   ├─ 파일명: {file_name}")
        logger.info(f"   ├─ 파일 크기: {audio_file.size:,} bytes")
        logger.info(f"   ├─ 파일 타입: {audio_file.content_type}")
        logger.info(f"   ├─ 보이스피싱 여부: {is_phishing}")
        logger.info(f"   ├─ 신뢰도: {final_confidence:.4f}")
        log_and_print("INFO", f"   Phishing Type: {llm_result['phishing_type']}")
        logger.info(f"   ├─ 전체 처리 시간: {total_processing_time:.2f}초")
        logger.info(f"   └─ 클라이언트 IP: {client_ip}")
        
        log_and_print("INFO", "[CREATE] Creating AnalysisResult record...")
        analysis_result = AnalysisResult.objects.create(
            file_name=file_name,  # 길이 제한된 파일명 사용
            file_size=audio_file.size,
            file_type=audio_file.content_type,
            is_phishing=is_phishing,
            confidence=final_confidence,
            phishing_type=llm_result['phishing_type'],
            stt_text=transcript,
            risk_factors=llm_result.get('risk_factors', ['기관명 언급', '계좌 관련 키워드'] if is_phishing else []),
            explanation=llm_result['explanation'],
            warning_message=llm_result['warning'],
            processing_time=total_processing_time,
            ip_address=client_ip
        )
        
        log_and_print("INFO", f"[SUCCESS] AnalysisResult Save Complete!")
        logger.info(f"   ├─ 레코드 ID: {analysis_result.id}")
        logger.info(f"   └─ 생성 시간: {analysis_result.created_at}")
        
        # 성공 로그
        logger.info("="*80)
        print_separator()
        log_and_print("INFO", "[SYSLOG] SystemLog Table Final Log Save")
        
        try:
            log_and_print("INFO", "[CREATE] Creating analysis complete log...")
            success_log = SystemLog.objects.create(
                level='INFO',
                message=f'분석 완료: {audio_file.name} - {"피싱" if is_phishing else "정상"} (신뢰도: {final_confidence:.3f})',
                file_name=audio_file.name,
                ip_address=client_ip
            )
            log_and_print("INFO", f"[SUCCESS] Analysis complete log save successful!")
            logger.info(f"   └─ 로그 ID: {success_log.id}")
        except Exception as log_error:
            log_and_print("ERROR", f"[ERROR] Analysis complete log save failed: {str(log_error)}")
        
        # 최종 분석 완료 요약
        logger.info("="*80)
        print_separator()
        log_and_print("INFO", "[COMPLETE] Analysis Complete - Overall Processing Summary")
        logger.info(f"   ├─ 요청 ID: {ocrn_no}")
        logger.info(f"   ├─ 파일명: {audio_file.name}")
        logger.info(f"   ├─ 전체 처리 시간: {total_processing_time:.2f}초")
        logger.info(f"   ├─ 최종 판정: {'보이스피싱' if is_phishing else '일반 통화'}")
        logger.info(f"   ├─ 신뢰도: {final_confidence:.4f} ({final_confidence*100:.2f}%)")
        logger.info(f"   ├─ 사용된 모델: {'1차+2차 모델' if dl_jdgm_yn == 'Y' else '1차 모델만'}")
        logger.info(f"   ├─ 저장된 테이블: ProcessdFile, InferenceResult, AnalysisResult, SystemLog")
        logger.info(f"   └─ 분석 결과 ID: {safe_rslt_id}")
        logger.info("="*80)
        
        # 분석 결과 반환
        result = {
            'success': True,
            'ocrn_no': ocrn_no,
            'rslt_id': safe_rslt_id,
            'is_phishing': is_phishing,
            'confidence': final_confidence,
            'type': llm_result['phishing_type'],
            'warning_message': llm_result['warning'],
            'explanation': llm_result['explanation'],
            'risk_factors': llm_result.get('risk_factors', ['기관명 언급', '계좌 관련 키워드'] if is_phishing else []),
            'processing_time': time.time() - start_time,
            'stt_text': transcript,
            'analysis_details': {
                'first_model': first_model_result,
                'second_model': second_model_result,
                'final_decision_by': '2차 모델 (LGBM)' if dl_jdgm_yn == 'Y' else '1차 모델 (Stacking)',
                'dl_judgment': dl_jdgm_yn == 'Y'
            },
            'file_info': {
                'name': file_name,
                'original_name': audio_file.name,
                'size': audio_file.size,
                'type': audio_file.content_type
            }
        }
        
        # 분석 완료 메시지 전송
        send_analysis_complete(ocrn_no, result)
        
        return JsonResponse(result)
        
    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)
        
        # 오류 메시지 전송 (ocrn_no가 생성된 경우만)
        if 'ocrn_no' in locals():
            send_analysis_error(ocrn_no, f"분석 중 오류가 발생했습니다: {error_message}")
        
        # 데이터베이스 관련 오류인지 확인
        if "Data too long" in error_message:
            logger.error(f"데이터베이스 필드 길이 초과 오류: {error_message}")
            user_error_message = "데이터 처리 중 길이 제한 오류가 발생했습니다. 시스템 관리자에게 문의해주세요."
            error_code = "DATA_LENGTH_ERROR"
        elif "1406" in error_message:
            logger.error(f"MySQL 데이터 길이 오류: {error_message}")
            user_error_message = "데이터베이스 저장 중 오류가 발생했습니다. 파일명이 너무 길거나 특수문자가 포함되어 있을 수 있습니다."
            error_code = "MYSQL_DATA_ERROR"
        elif "Connection" in error_message or "timeout" in error_message.lower():
            logger.error(f"데이터베이스 연결 오류: {error_message}")
            user_error_message = "데이터베이스 연결에 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
            error_code = "DB_CONNECTION_ERROR"
        else:
            logger.error(f"일반적인 분석 오류 ({error_type}): {error_message}")
            user_error_message = "분석 처리 중 예상치 못한 오류가 발생했습니다. 다시 시도해주세요."
            error_code = "GENERAL_ERROR"
        
        # 상세 오류 로그
        try:
            SystemLog.objects.create(
                level='ERROR',
                message=f'[{error_type}] {error_message}',
                file_name=locals().get('audio_file', {}).get('name', 'UNKNOWN') if 'audio_file' in locals() else 'UNKNOWN',
                ip_address=client_ip
            )
        except Exception as log_error:
            logger.error(f"오류 로그 저장 실패: {str(log_error)}")
        
        logger.error(f"Analysis error details: type={error_type}, message={error_message}")
        
        return JsonResponse({
            'success': False,
            'error': user_error_message,
            'debug_info': {
                'error_type': error_type,
                'error_code': error_code
            } if settings.DEBUG else {}
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def submit_feedback(request):
    """피드백 제출 API - 개선된 버전"""
    client_ip = get_client_ip(request)
    
    try:
        # JSON 데이터 파싱 (UTF-8 인코딩 보장)
        try:
            # 요청 바디를 UTF-8로 디코딩
            body_text = request.body.decode('utf-8')
            data = json.loads(body_text)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"피드백 데이터 파싱 실패: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': '잘못된 데이터 형식입니다.'
            }, status=400)
        
        # 필수 데이터 추출 및 검증
        rslt_id = data.get('rslt_id')
        ocrn_no = data.get('ocrn_no')
        user_prediction = data.get('user_prediction', 'N')
        comment = data.get('comment', '').strip()
        
        # 한글 텍스트 안전하게 처리
        if comment:
            try:
                # UTF-8 인코딩/디코딩 테스트
                comment.encode('utf-8').decode('utf-8')
            except UnicodeError:
                logger.warning("잘못된 UTF-8 인코딩의 코멘트 감지, 안전한 문자로 대체")
                comment = comment.encode('utf-8', errors='ignore').decode('utf-8')
            
            # 추가 정제: 제어 문자 제거
            import re
            comment = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', comment)
        
        # 피드백 제출 시작 로깅
        logger.info("="*80)
        print_separator()
        log_and_print("INFO", "[FEEDBACK] Feedback Submission Stage Started")
        logger.info(f"   ├─ 결과 ID: {rslt_id}")
        logger.info(f"   ├─ 요청 번호: {ocrn_no}")
        logger.info(f"   ├─ 사용자 판단: {user_prediction}")
        logger.info(f"   ├─ 코멘트 길이: {len(comment)} 글자")
        logger.info(f"   └─ 클라이언트 IP: {client_ip}")
        
        # 필수 정보 검증
        if not rslt_id or not ocrn_no:
            log_and_print("WARNING", "[ERROR] Required feedback information missing")
            logger.warning(f"   ├─ rslt_id: {rslt_id}")
            logger.warning(f"   └─ ocrn_no: {ocrn_no}")
            return JsonResponse({
                'success': False,
                'error': '분석 결과 정보가 누락되었습니다. 페이지를 새로고침 후 다시 시도해주세요.'
            }, status=400)
        
        # 분석 결과 존재 여부 확인 (더 유연한 검색)
        log_and_print("INFO", "[SEARCH] Searching for analysis results...")
        try:
            # 먼저 rslt_id로 검색
            logger.info(f"   └─ rslt_id로 검색: {rslt_id}")
            inference_result = InferenceResult.objects.filter(rslt_id=rslt_id).first()
            
            if not inference_result:
                # rslt_id로 못 찾으면 ocrn_no로 검색
                logger.info(f"   └─ ocrn_no로 검색: {ocrn_no}")
                inference_result = InferenceResult.objects.filter(
                    ocrn_no__ocrn_no=ocrn_no
                ).first()
            
            if not inference_result:
                # 그래도 못 찾으면 file_id로 검색
                logger.info(f"   └─ file_id로 검색: {ocrn_no}")
                inference_result = InferenceResult.objects.filter(file_id=ocrn_no).first()
            
            if not inference_result:
                log_and_print("ERROR", "[ERROR] Cannot find corresponding analysis result")
                logger.error(f"   ├─ 검색한 rslt_id: {rslt_id}")
                logger.error(f"   └─ 검색한 ocrn_no: {ocrn_no}")
                
                total_results = InferenceResult.objects.count()
                logger.info(f"[INFO] 전체 InferenceResult 개수: {total_results}")
                
                # 최근 결과들 확인을 위한 로그
                recent_results = InferenceResult.objects.order_by('-prdt_dt')[:5]
                logger.info("[INFO] 최근 분석 결과 5개:")
                for i, result in enumerate(recent_results, 1):
                    logger.info(f"   {i}. rslt_id={result.rslt_id}, ocrn_no={result.ocrn_no.ocrn_no}, file_id={result.file_id}")
                
                return JsonResponse({
                    'success': False,
                    'error': '해당 분석 결과를 찾을 수 없습니다. 분석이 완료되지 않았거나 오류가 발생했을 수 있습니다.'
                }, status=404)
            else:
                log_and_print("INFO", "[SUCCESS] Analysis result search successful")
                logger.info(f"   ├─ 발견된 결과 ID: {inference_result.id}")
                logger.info(f"   ├─ rslt_id: {inference_result.rslt_id}")
                logger.info(f"   └─ 예측 점수: {inference_result.prdt_scr:.4f}")
                
        except Exception as db_error:
            logger.error(f"분석 결과 검색 중 데이터베이스 오류: {str(db_error)}")
            return JsonResponse({
                'success': False,
                'error': '데이터베이스 오류가 발생했습니다.'
            }, status=500)
        
        # 사용자 예측 값 검증
        if user_prediction not in ['Y', 'N']:
            logger.warning(f"잘못된 사용자 예측 값: {user_prediction}")
            user_prediction = 'N'  # 기본값으로 설정
        
        # 코멘트 길이 제한 (1000자)
        if len(comment) > 1000:
            comment = comment[:1000]
            logger.info(f"코멘트 길이 제한으로 자름: {len(data.get('comment', ''))} -> 1000")
        
        # 중복 피드백 확인 (선택적 - 같은 결과에 대한 중복 피드백 방지)
        log_and_print("INFO", "[CHECK] Checking for duplicate feedback...")
        existing_feedback = Feedback.objects.filter(
            rslt_id=rslt_id,
            ocrn_no=ocrn_no
        ).first()
        
        if existing_feedback:
            log_and_print("INFO", "[UPDATE] Existing feedback update mode")
            logger.info(f"   ├─ 기존 피드백 ID: {existing_feedback.prp_no}")
            logger.info(f"   ├─ 기존 사용자 판단: {existing_feedback.prdt_rslt_yn}")
            logger.info(f"   └─ 새로운 사용자 판단: {user_prediction}")
            
            # 기존 피드백 업데이트
            existing_feedback.prdt_rslt_yn = user_prediction
            existing_feedback.wropn_cn = comment
            existing_feedback.opnn_reg_ymd = timezone.now()
            existing_feedback.save()
            
            feedback_id = existing_feedback.prp_no
            message = '피드백이 성공적으로 업데이트되었습니다.'
            
            log_and_print("INFO", "[SUCCESS] Existing feedback update complete")
            logger.info(f"   └─ 업데이트된 피드백 ID: {feedback_id}")
        else:
            log_and_print("INFO", "[CREATE] New feedback creation mode")
            
            # 새로운 피드백 생성 (prp_no는 20자 제한이므로 짧은 ID 사용)
            prp_no = generate_short_id()  # 기존 함수 재사용
            logger.info(f"   ├─ 생성할 피드백 ID: {prp_no}")
            logger.info(f"   ├─ 사용자 판단: {user_prediction}")
            logger.info(f"   └─ 코멘트 길이: {len(comment)} 글자")
            
            feedback = Feedback.objects.create(
                prp_no=prp_no,
                rslt_id=rslt_id,
                ocrn_no=ocrn_no,
                prdt_rslt_yn=user_prediction,
                wropn_cn=comment,
                opnn_reg_ymd=timezone.now()
            )
            
            feedback_id = prp_no
            message = '피드백이 성공적으로 제출되었습니다.'
            
            log_and_print("INFO", "[SUCCESS] New feedback creation complete")
            logger.info(f"   ├─ 생성된 피드백 레코드 ID: {feedback.id}")
            logger.info(f"   └─ 피드백 ID: {feedback_id}")
            
            log_system_info("INFO", f"새 피드백 생성: {prp_no} - 사용자 판단: {user_prediction}", inference_result.ocrn_no.trsc_file_nm if inference_result.ocrn_no else "UNKNOWN", client_ip)
        
        # 시스템 로그 기록
        log_and_print("INFO", "[SYSLOG] Saving feedback complete log to SystemLog table...")
        try:
            system_log = SystemLog.objects.create(
                level='INFO',
                message=f'피드백 제출 완료: {feedback_id} - 사용자 판단: {user_prediction}',
                file_name=inference_result.ocrn_no.trsc_file_nm,
                ip_address=client_ip
            )
            log_and_print("INFO", f"[SUCCESS] SystemLog save successful (ID: {system_log.id})")
        except Exception as log_error:
            logger.error(f"[ERROR] 피드백 SystemLog 기록 실패: {str(log_error)}")
        
        # 피드백 제출 완료 요약
        logger.info("="*80)
        print_separator()
        log_and_print("INFO", "[COMPLETE] Feedback Submission Complete - Summary")
        logger.info(f"   ├─ 피드백 ID: {feedback_id}")
        logger.info(f"   ├─ 처리 방식: {'업데이트' if existing_feedback else '신규 생성'}")
        logger.info(f"   ├─ 사용자 판단: {user_prediction} ({'보이스피싱' if user_prediction == 'Y' else '일반통화'})")
        logger.info(f"   ├─ 코멘트: {'있음' if comment else '없음'}")
        logger.info(f"   └─ 메시지: {message}")
        logger.info("="*80)
        
        return JsonResponse({
            'success': True,
            'message': message,
            'feedback_id': feedback_id,
            'data': {
                'rslt_id': rslt_id,
                'user_prediction': user_prediction,
                'has_comment': len(comment) > 0
            }
        })
        
    except Exception as e:
        logger.error(f"피드백 제출 중 예상치 못한 오류: {str(e)}")
        logger.error(f"오류 타입: {type(e).__name__}")
        
        # 스택 트레이스도 로그에 기록
        import traceback
        logger.error(f"스택 트레이스: {traceback.format_exc()}")
        
        # 오류 로그 기록 시도
        try:
            SystemLog.objects.create(
                level='ERROR',
                message=f'피드백 제출 오류: {type(e).__name__}: {str(e)}',
                file_name='FEEDBACK_ERROR',
                ip_address=client_ip
            )
        except:
            pass  # 로그 저장 실패해도 응답은 반환
        
        return JsonResponse({
            'success': False,
            'error': '피드백 제출 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
            'debug_error': str(e) if settings.DEBUG else None
        }, status=500)


def get_analysis_history(request):
    """분석 이력 조회 API"""
    try:
        # 최근 분석 결과들 가져오기
        results = InferenceResult.objects.select_related('ocrn_no').order_by('-prdt_dt')[:50]
        
        history = []
        for result in results:
            history.append({
                'rslt_id': result.rslt_id,
                'ocrn_no': result.ocrn_no.ocrn_no,
                'file_name': result.ocrn_no.trsc_file_nm,
                'is_phishing': result.ml_rslt_cd == '1',
                'confidence': float(result.prdt_scr),
                'phishing_type': result.phsh_tp_nm,
                'warning': result.warn_cn,
                'transcript': result.ocrn_no.transcript[:200] + '...' if len(result.ocrn_no.transcript) > 200 else result.ocrn_no.transcript,
                'created_at': result.prdt_dt.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        logger.error(f"History retrieval error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'이력 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


def statistics(request):
    """통계 페이지"""
    total_analyses = AnalysisResult.objects.count()
    phishing_count = AnalysisResult.objects.filter(is_phishing=True).count()
    normal_count = AnalysisResult.objects.filter(is_phishing=False).count()
    
    # 새로운 통계도 추가
    total_processed = ProcessdFile.objects.count()
    total_inferences = InferenceResult.objects.count()
    total_feedbacks = Feedback.objects.count()
    
    context = {
        'total_analyses': total_analyses,
        'phishing_count': phishing_count,
        'normal_count': normal_count,
        'phishing_rate': (phishing_count / total_analyses * 100) if total_analyses > 0 else 0,
        'total_processed': total_processed,
        'total_inferences': total_inferences,
        'total_feedbacks': total_feedbacks,
    }
    
    return render(request, 'voice_phishing/statistics.html', context)


