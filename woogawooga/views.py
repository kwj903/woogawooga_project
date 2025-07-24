from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import (
    AnalysisResult, SystemLog, ProcessdFile, InferenceResult, 
    ModelRegistry, Feedback, VoicePhishingSystemLog
)
import json
import time
import random
import logging
import uuid
import pickle
import os
from pathlib import Path
import numpy as np
from datetime import datetime
import requests
import tempfile
from django.conf import settings

# 머신러닝 및 자연어 처리
try:
    from kiwipiepy import Kiwi
    import lightgbm as lgb
except ImportError as e:
    logger.warning(f"필수 패키지 import 실패: {e}")

# 로거 설정
logger = logging.getLogger(__name__)

# 로깅 레벨 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 모델 로드 (전역 변수로 한 번만 로드)
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / 'models' / 'stacking_v2.pkl'
LGBM_MODEL_PATH = BASE_DIR / 'models' / 'lgbm_model_v2.pkl'
TFIDF_PATH = BASE_DIR / 'datas' / 'modelsData' / 'tfidf_vectorizer.pkl'

# 모델 전역 변수
stacking_model = None
lgbm_model = None
tfidf_vectorizer = None
kiwi_tokenizer = None

def load_models():
    """모든 필수 모델 및 토크나이저 로드"""
    global stacking_model, lgbm_model, tfidf_vectorizer, kiwi_tokenizer
    
    try:
        # 1차 Stacking 모델 로드
        if stacking_model is None and MODEL_PATH.exists():
            with open(MODEL_PATH, 'rb') as f:
                stacking_model = pickle.load(f)
                logger.info("1차 Stacking 모델 로드 완료")
        elif not MODEL_PATH.exists():
            logger.warning(f"1차 모델 파일 없음: {MODEL_PATH}")
        
        # 2차 LightGBM 모델 로드
        if lgbm_model is None and LGBM_MODEL_PATH.exists():
            try:
                lgbm_model = lgb.Booster(model_file=str(LGBM_MODEL_PATH))
                logger.info("2차 LightGBM 모델 로드 완료")
            except Exception as e:
                logger.error(f"LightGBM 모델 로드 실패: {e}")
        elif not LGBM_MODEL_PATH.exists():
            logger.warning(f"2차 모델 파일 없음: {LGBM_MODEL_PATH}")
        
        # TF-IDF 벡터라이저 로드
        if tfidf_vectorizer is None and TFIDF_PATH.exists():
            with open(TFIDF_PATH, 'rb') as f:
                tfidf_vectorizer = pickle.load(f)
                logger.info("TF-IDF 벡터라이저 로드 완료")
        elif not TFIDF_PATH.exists():
            logger.warning(f"TF-IDF 파일 없음: {TFIDF_PATH}")
        
        # KiWi 토크나이저 초기화
        if kiwi_tokenizer is None:
            try:
                kiwi_tokenizer = Kiwi()
                logger.info("KiWi 토크나이저 초기화 완료")
            except Exception as e:
                logger.error(f"KiWi 토크나이저 초기화 실패: {e}")
                
    except Exception as e:
        logger.error(f"모델 로드 중 전체 오류: {str(e)}")

def preprocess_text(text):
    """KiWi를 사용한 텍스트 전처리"""
    if not text or not text.strip():
        return {"tokens": [], "vector": [], "processed_text": ""}
    
    try:
        # 모델 로드 확인
        if not kiwi_tokenizer:
            load_models()
        
        # KiWi 토큰화
        tokens = []
        processed_words = []
        
        if kiwi_tokenizer:
            # KiWi로 형태소 분석
            result = kiwi_tokenizer.analyze(text)
            
            for token in result[0][0]:  # 첫 번째 분석 결과 사용
                # 명사, 동사, 형용사, 부사만 추출
                if token.tag in ['NNP', 'NNG', 'VV', 'VA', 'VX', 'VCP', 'VCN', 'MAG', 'MAJ']:
                    word = token.form.strip()
                    if len(word) > 1:  # 한 글자 단어 제외
                        tokens.append(word)
                        processed_words.append(word)
        else:
            # KiWi가 없을 경우 기본 분할
            logger.warning("KiWi 토크나이저가 로드되지 않음. 기본 분할 사용")
            tokens = text.split()
            processed_words = tokens
        
        # 전처리된 텍스트 생성
        processed_text = ' '.join(processed_words)
        
        # TF-IDF 벡터화
        vector = []
        try:
            if tfidf_vectorizer and processed_text:
                vector = tfidf_vectorizer.transform([processed_text]).toarray()[0].tolist()
            else:
                vector = [0.0] * 1000  # 기본 벡터 크기
        except Exception as e:
            logger.error(f"TF-IDF 벡터화 실패: {e}")
            vector = [0.0] * 1000
        
        logger.info(f"텍스트 전처리 완료: 원본 길이={len(text)}, 토큰 수={len(tokens)}")
        
        return {
            "tokens": tokens,
            "vector": vector,
            "processed_text": processed_text
        }
        
    except Exception as e:
        logger.error(f"텍스트 전처리 실패: {str(e)}")
        return {
            "tokens": text.split() if text else [],
            "vector": [0.0] * 1000,
            "processed_text": text
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
                
                if response.status_code != 200:
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
        
        # 모델 로드 확인
        if not stacking_model or not tfidf_vectorizer:
            load_models()
        
        if not stacking_model:
            logger.error("1차 Stacking 모델이 로드되지 않음")
            raise Exception("1차 모델 로드 실패")
        
        if not tfidf_vectorizer:
            logger.error("TF-IDF 벡터라이저가 로드되지 않음")
            raise Exception("TF-IDF 벡터라이저 로드 실패")
        
        # 텍스트 전처리
        preprocessed = preprocess_text(text)
        processed_text = preprocessed.get('processed_text', text)
        
        if not processed_text.strip():
            logger.warning("전처리된 텍스트가 비어있음")
            processed_text = text
        
        logger.info(f"전처리 완료: 원본 길이={len(text)}, 처리 후 길이={len(processed_text)}")
        
        # TF-IDF 변환
        X = tfidf_vectorizer.transform([processed_text])
        logger.info(f"TF-IDF 벡터 형태: {X.shape}")
        
        # 예측 수행
        prediction = stacking_model.predict(X)[0]
        probability = stacking_model.predict_proba(X)[0]
        
        # 피싱일 확률 (클래스 1의 확률)
        phishing_probability = probability[1] if len(probability) > 1 else 0.5
        
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
        return {
            'prediction': -1,  # 보류 상태
            'confidence': 0.5,
            'probabilities': [0.5, 0.5],
            'decision_type': "error_fallback",
            'error': str(e),
            'model_used': 'stacking_v2_failed'
        }

def analyze_with_second_model(text):
    """2차 LightGBM 모델 분석"""
    try:
        logger.info("2차 모델 분석 시작")
        
        # 모델 로드 확인
        if not lgbm_model:
            load_models()
        
        if not lgbm_model:
            logger.error("2차 LightGBM 모델이 로드되지 않음")
            # 2차 모델이 없으면 1차 모델 결과를 기반으로 판별
            return {
                'prediction': 1,  # 보수적으로 피싱으로 판별
                'confidence': 0.6,
                'decision_type': "fallback_conservative",
                'model_used': 'lgbm_v2_fallback',
                'error': '2차 모델 로드 실패'
            }
        
        # 텍스트 전처리
        preprocessed = preprocess_text(text)
        processed_text = preprocessed.get('processed_text', text)
        
        if not processed_text.strip():
            logger.warning("2차 모델용 전처리된 텍스트가 비어있음")
            processed_text = text
        
        logger.info(f"2차 모델 전처리 완료: 처리 후 길이={len(processed_text)}")
        
        # LightGBM은 벡터 형태의 입력이 필요하므로 TF-IDF 벡터 사용
        if not tfidf_vectorizer:
            logger.error("TF-IDF 벡터라이저가 없어 2차 모델 분석 불가")
            return {
                'prediction': 1,
                'confidence': 0.6,
                'decision_type': "fallback_no_vectorizer",
                'model_used': 'lgbm_v2_fallback'
            }
        
        # TF-IDF 벡터화
        X = tfidf_vectorizer.transform([processed_text])
        
        # LightGBM 예측 수행
        # predict() 메소드는 확률을 반환하므로 임계값으로 판별
        prediction_proba = lgbm_model.predict(X.toarray())[0]
        
        # 확률을 0-1 범위로 정규화 (필요시)
        if prediction_proba < 0:
            prediction_proba = 0
        elif prediction_proba > 1:
            prediction_proba = 1
            
        # 임계값 0.5로 최종 판별
        SECOND_MODEL_THRESHOLD = 0.5
        final_prediction = 1 if prediction_proba >= SECOND_MODEL_THRESHOLD else 0
        
        decision_type = "second_model_phishing" if final_prediction == 1 else "second_model_normal"
        
        result = {
            'prediction': final_prediction,
            'confidence': float(prediction_proba),
            'decision_type': decision_type,
            'threshold': SECOND_MODEL_THRESHOLD,
            'model_used': 'lgbm_v2',
            'processed_text_length': len(processed_text)
        }
        
        logger.info(f"2차 모델 분석 완료: 예측={final_prediction}, 확률={prediction_proba:.3f}")
        return result
        
    except Exception as e:
        logger.error(f"2차 모델 분석 실패: {str(e)}")
        
        # 실패 시 보수적으로 피싱으로 판별
        return {
            'prediction': 1,
            'confidence': 0.7,
            'decision_type': "error_conservative",
            'model_used': 'lgbm_v2_failed',
            'error': str(e)
        }

def generate_llm_explanation(text, first_result, second_result=None):
    """1차/2차 모델 결과를 기반으로 한 임시 설명 생성 (추후 LLM 구현 예정)"""
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
        
        # 피싱 유형별 메시지 템플릿
        phishing_types = ['기관사칭형', '대출빙자형', '투자빙자형', '선납금요구형']
        
        if final_prediction == 1:  # 보이스피싱
            phishing_type = random.choice(phishing_types)
            
            # 신뢰도에 따른 경고 메시지 생성
            if confidence >= 0.8:
                warning = f"⚠️ 고위험: 보이스피싱 가능성이 매우 높습니다 (신뢰도: {confidence:.1%}). 즉시 통화를 종료하고 해당 기관에 직접 확인하시기 바랍니다."
            elif confidence >= 0.6:
                warning = f"⚠️ 중위험: 보이스피싱 가능성이 높습니다 (신뢰도: {confidence:.1%}). 통화 내용을 신중히 검토하고 의심스러우면 통화를 종료하세요."
            else:
                warning = f"⚠️ 저위험: 보이스피싱 가능성이 있습니다 (신뢰도: {confidence:.1%}). 개인정보 제공에 주의하시기 바랍니다."
            
            explanation = f"{decision_source}에서 '{phishing_type}' 패턴으로 분류되었습니다. 기관명 사칭, 개인정보 요구, 금전 관련 유도 등의 의심 요소가 감지되었습니다."
            
            risk_factors = [
                "기관명 언급",
                "계좌번호 요구",
                "개인정보 확인 요청",
                "금전 관련 언급"
            ]
            
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
        
        result = {
            'phishing_type': phishing_type,
            'warning': warning,
            'explanation': explanation,
            'risk_factors': risk_factors,
            'analysis_process': process_info,
            'confidence_level': confidence,
            'decision_source': decision_source,
            'note': '※ 이 결과는 AI 모델 기반 분석이며, 추후 LLM 기반 상세 설명으로 업그레이드 예정입니다.'
        }
        
        logger.info(f"설명 생성 완료: {phishing_type}, 신뢰도: {confidence:.3f}")
        return result
        
    except Exception as e:
        logger.error(f"설명 생성 실패: {str(e)}")
        
        # 오류 시 기본 응답
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


@csrf_exempt
@require_http_methods(["POST"])
def analyze(request):
    """음성 파일 분석 API"""
    start_time = time.time()
    client_ip = get_client_ip(request)
    ocrn_no = str(uuid.uuid4())  # 고유 발생번호 생성
    
    logger.info(f"=== 분석 요청 시작 ===")
    logger.info(f"클라이언트 IP: {client_ip}")
    logger.info(f"발생번호 (ocrn_no): {ocrn_no} (길이: {len(ocrn_no)})")
    logger.info(f"요청 메서드: {request.method}")
    logger.info(f"콘텐츠 타입: {request.content_type}")
    
    try:
        # 업로드된 파일 확인
        if 'audio_file' not in request.FILES:
            VoicePhishingSystemLog.objects.create(
                log_nm='AUDIO_FILE_MISSING',
                ocrn_no_id=ocrn_no,
                log_reg_dt=timezone.now(),
                log_ocrn_pstn='UPLOAD_VALIDATION',
                err_rsn='오디오 파일이 업로드되지 않음'
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
            VoicePhishingSystemLog.objects.create(
                log_nm='INVALID_FILE_FORMAT',
                ocrn_no_id=ocrn_no,
                log_reg_dt=timezone.now(),
                log_ocrn_pstn='FILE_VALIDATION',
                err_rsn=f'지원하지 않는 파일 형식: {file_extension}'
            )
            return JsonResponse({
                'success': False,
                'error': f'지원하지 않는 파일 형식입니다. 지원 형식: {", ".join(allowed_extensions)}'
            }, status=400)
        
        # 파일 크기 검증 (50MB 제한)
        max_size = 50 * 1024 * 1024  # 50MB
        if audio_file.size > max_size:
            VoicePhishingSystemLog.objects.create(
                log_nm='FILE_SIZE_EXCEEDED',
                ocrn_no_id=ocrn_no,
                log_reg_dt=timezone.now(),
                log_ocrn_pstn='FILE_VALIDATION',
                err_rsn=f'파일 크기 초과: {audio_file.size} bytes'
            )
            return JsonResponse({
                'success': False,
                'error': '파일 크기가 너무 큽니다. 최대 50MB까지 지원합니다.'
            }, status=400)
        
        # 1단계: 오디오 파일 저장
        upload_dir = BASE_DIR / 'media' / 'uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        saved_file_path = upload_dir / f"{ocrn_no}_{audio_file.name}"
        with open(saved_file_path, 'wb') as f:
            for chunk in audio_file.chunks():
                f.write(chunk)
        
        logger.info(f"오디오 파일 저장: {saved_file_path}")
        
        # 2단계: STT 처리
        try:
            logger.info(f"VITO STT 시작: {audio_file.name}")
            transcript = vito_stt(audio_file)
            logger.info(f"VITO STT 완료: {len(transcript)} 글자")
        except Exception as e:
            VoicePhishingSystemLog.objects.create(
                log_nm='STT_PROCESSING_ERROR',
                ocrn_no_id=ocrn_no,
                log_reg_dt=timezone.now(),
                log_ocrn_pstn='STT_MODULE',
                err_rsn=f'STT 처리 실패: {str(e)}'
            )
            logger.error(f"VITO STT 실패: {str(e)}")
            transcript = "STT 처리에 실패했습니다."
        
        # 3단계: 텍스트 전처리
        prcs_cont_1 = preprocess_text(transcript)
        prcs_cont_2 = {"processed_text": transcript}  # 2차 전처리는 임시
        
        # 4단계: 파일 정보 저장 (파일명 길이 제한 처리)
        file_name = audio_file.name
        if len(file_name) > 295:  # 300자 제한에서 여유분 5자
            file_name = file_name[:295] + "..."
            logger.warning(f"파일명 길이 제한으로 자름: 원본 {len(audio_file.name)}자 -> {len(file_name)}자")
        
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
        
        # 5단계: 1차 모델 분석
        logger.info("1차 모델 분석 시작")
        first_model_result = analyze_with_first_model(transcript)
        logger.info(f"1차 모델 분석 완료: {first_model_result}")
        
        # 6단계: 2차 모델 분석 (조건부 실행)
        second_model_result = None
        final_prediction = first_model_result['prediction']
        final_confidence = first_model_result['confidence']
        dl_jdgm_yn = 'N'  # 딥러닝 판단 여부
        
        if first_model_result['prediction'] == -1:  # 보류 구간
            logger.info("보류 구간 - 2차 모델 분석 시작")
            second_model_result = analyze_with_second_model(transcript)
            logger.info(f"2차 모델 분석 완료: {second_model_result}")
            
            # 2차 모델 결과를 최종 결과로 사용
            final_prediction = second_model_result['prediction']
            final_confidence = second_model_result['confidence']
            dl_jdgm_yn = 'Y'
        else:
            logger.info(f"1차 모델에서 즉시 판별: {first_model_result['decision_type']}")
        
        # 7단계: LLM 설명 생성 (임시)
        logger.info("LLM 설명 생성 시작")
        llm_result = generate_llm_explanation(transcript, first_model_result, second_model_result)
        logger.info(f"LLM 설명 생성 완료: {llm_result}")
        
        # 8단계: ModelRegistry 등록
        # 1차 모델 등록
        first_model_registry, created = ModelRegistry.objects.get_or_create(
            mdl_id='STACKING_V2',
            defaults={
                'mdl_nm': 'Stacking Classifier V2 (1차 모델)',
                'use_yn': 'Y'
            }
        )
        if created:
            logger.info("1차 모델이 ModelRegistry에 등록됨")
        
        # 2차 모델 등록 (사용된 경우만)
        if dl_jdgm_yn == 'Y':
            second_model_registry, created = ModelRegistry.objects.get_or_create(
                mdl_id='LGBM_V2',
                defaults={
                    'mdl_nm': 'LightGBM Model V2 (2차 모델)',
                    'use_yn': 'Y'
                }
            )
            if created:
                logger.info("2차 모델이 ModelRegistry에 등록됨")
        
        # 9단계: 추론 결과 저장
        rslt_id = str(uuid.uuid4())
        
        # 최종 결과를 문자열로 변환 (데이터베이스 저장용)
        ml_result_code = str(final_prediction) if final_prediction != -1 else '보류'
        
        # 필드 길이 안전장치 적용
        safe_rslt_id = safe_truncate_field(rslt_id, 50, "rslt_id")
        safe_file_id_value = safe_file_id(ocrn_no)
        safe_mdl_id = safe_truncate_field('LGBM_V2' if dl_jdgm_yn == 'Y' else 'STACKING_V2', 20, "mdl_id")
        safe_ml_rslt_cd = safe_truncate_field(ml_result_code, 10, "ml_rslt_cd")
        safe_phsh_tp_nm = safe_truncate_field(llm_result['phishing_type'], 100, "phsh_tp_nm")
        
        logger.info(f"InferenceResult 저장 데이터 길이 검증: rslt_id={len(safe_rslt_id)}, file_id={len(safe_file_id_value)}, mdl_id={len(safe_mdl_id)}")
        
        try:
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
            logger.info(f"InferenceResult 저장 성공: {safe_rslt_id}")
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
        is_phishing = final_prediction == 1
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
            processing_time=time.time() - start_time,
            ip_address=client_ip
        )
        
        # 성공 로그
        VoicePhishingSystemLog.objects.create(
            log_nm='ANALYSIS_COMPLETED',
            ocrn_no=processed_file,
            log_reg_dt=timezone.now(),
            log_ocrn_pstn='ANALYSIS_MODULE',
            err_rsn=f'분석 완료: {audio_file.name} - {"피싱" if is_phishing else "정상"}'
        )
        
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
        
        return JsonResponse(result)
        
    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)
        
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
            VoicePhishingSystemLog.objects.create(
                log_nm='ANALYSIS_ERROR',
                ocrn_no_id=ocrn_no if 'ocrn_no' in locals() else None,
                log_reg_dt=timezone.now(),
                log_ocrn_pstn='ANALYSIS_MODULE',
                err_rsn=f'[{error_type}] {error_message}',
                err_cd_nm=error_code
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
        # JSON 데이터 파싱
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("피드백 데이터 JSON 파싱 실패")
            return JsonResponse({
                'success': False,
                'error': '잘못된 데이터 형식입니다.'
            }, status=400)
        
        # 필수 데이터 추출 및 검증
        rslt_id = data.get('rslt_id')
        ocrn_no = data.get('ocrn_no')
        user_prediction = data.get('user_prediction', 'N')
        comment = data.get('comment', '').strip()
        
        logger.info(f"피드백 제출 요청: rslt_id={rslt_id}, ocrn_no={ocrn_no}, prediction={user_prediction}")
        
        # 필수 정보 검증
        if not rslt_id or not ocrn_no:
            logger.warning(f"피드백 필수 정보 누락: rslt_id={rslt_id}, ocrn_no={ocrn_no}")
            return JsonResponse({
                'success': False,
                'error': '분석 결과 정보가 누락되었습니다. 페이지를 새로고침 후 다시 시도해주세요.'
            }, status=400)
        
        # 분석 결과 존재 여부 확인
        try:
            inference_result = InferenceResult.objects.get(
                rslt_id=rslt_id,
                ocrn_no__ocrn_no=ocrn_no
            )
        except InferenceResult.DoesNotExist:
            logger.error(f"해당 분석 결과를 찾을 수 없음: rslt_id={rslt_id}, ocrn_no={ocrn_no}")
            return JsonResponse({
                'success': False,
                'error': '해당 분석 결과를 찾을 수 없습니다.'
            }, status=404)
        
        # 사용자 예측 값 검증
        if user_prediction not in ['Y', 'N']:
            logger.warning(f"잘못된 사용자 예측 값: {user_prediction}")
            user_prediction = 'N'  # 기본값으로 설정
        
        # 코멘트 길이 제한 (1000자)
        if len(comment) > 1000:
            comment = comment[:1000]
            logger.info(f"코멘트 길이 제한으로 자름: {len(data.get('comment', ''))} -> 1000")
        
        # 중복 피드백 확인 (선택적 - 같은 결과에 대한 중복 피드백 방지)
        existing_feedback = Feedback.objects.filter(
            rslt_id=rslt_id,
            ocrn_no=ocrn_no
        ).first()
        
        if existing_feedback:
            logger.info(f"기존 피드백 업데이트: {existing_feedback.prp_no}")
            # 기존 피드백 업데이트
            existing_feedback.prdt_rslt_yn = user_prediction
            existing_feedback.wropn_cn = comment
            existing_feedback.opnn_reg_ymd = timezone.now()
            existing_feedback.save()
            
            feedback_id = existing_feedback.prp_no
            message = '피드백이 성공적으로 업데이트되었습니다.'
        else:
            # 새로운 피드백 생성
            prp_no = str(uuid.uuid4())
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
            logger.info(f"새 피드백 생성: {prp_no}")
        
        # 시스템 로그 기록
        try:
            VoicePhishingSystemLog.objects.create(
                log_nm='FEEDBACK_SUBMITTED',
                ocrn_no=inference_result.ocrn_no,
                log_reg_dt=timezone.now(),
                log_ocrn_pstn='FEEDBACK_MODULE',
                err_rsn=f'피드백 제출 완료: {feedback_id} - 사용자 판단: {user_prediction}'
            )
        except Exception as log_error:
            logger.error(f"피드백 시스템 로그 기록 실패: {str(log_error)}")
        
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
        
        # 오류 로그 기록 시도
        try:
            VoicePhishingSystemLog.objects.create(
                log_nm='FEEDBACK_ERROR',
                ocrn_no_id=data.get('ocrn_no') if 'data' in locals() else None,
                log_reg_dt=timezone.now(),
                log_ocrn_pstn='FEEDBACK_MODULE',
                err_rsn=f'피드백 제출 오류: {str(e)}',
                err_cd_nm='FEEDBACK_SUBMISSION_ERROR'
            )
        except:
            pass  # 로그 저장 실패해도 응답은 반환
        
        return JsonResponse({
            'success': False,
            'error': '피드백 제출 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
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
