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

# 로거 설정
logger = logging.getLogger(__name__)

# 모델 로드 (전역 변수로 한 번만 로드)
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / 'models' / 'stacking_v2.pkl'
TFIDF_PATH = BASE_DIR / 'datas' / 'modelsData' / 'tfidf_vectorizer.pkl'

# 모델 전역 변수
stacking_model = None
tfidf_vectorizer = None

def load_models():
    """1차 모델 및 TF-IDF 벡터라이저 로드"""
    global stacking_model, tfidf_vectorizer
    
    try:
        if stacking_model is None and MODEL_PATH.exists():
            with open(MODEL_PATH, 'rb') as f:
                stacking_model = pickle.load(f)
                logger.info("1차 모델 로드 완료")
        
        if tfidf_vectorizer is None and TFIDF_PATH.exists():
            with open(TFIDF_PATH, 'rb') as f:
                tfidf_vectorizer = pickle.load(f)
                logger.info("TF-IDF 벡터라이저 로드 완료")
                
    except Exception as e:
        logger.error(f"모델 로드 실패: {str(e)}")

def preprocess_text(text):
    """텍스트 전처리 (임시 구현)"""
    if not text:
        return {"tokens": [], "vector": []}
    
    # 간단한 전처리 (실제로는 KiWi 등 사용)
    tokens = text.split()
    
    # TF-IDF 벡터화
    try:
        if tfidf_vectorizer:
            vector = tfidf_vectorizer.transform([text]).toarray()[0].tolist()
        else:
            vector = [0.0] * 1000  # 기본 벡터 크기
    except:
        vector = [0.0] * 1000
    
    return {
        "tokens": tokens,
        "vector": vector
    }

def vito_stt(audio_file):
    """VITO STT 처리 (임시 구현)"""
    # 실제로는 VITO API 호출
    mock_responses = [
        "안녕하세요. 저는 금융감독원에서 나온 김철수입니다. 고객님의 계좌에 이상 거래가 발견되어 연락드렸습니다.",
        "고객님께서 문의하신 상품에 대해 안내드리겠습니다.",
        "보안을 위해 계좌번호와 비밀번호를 확인해주시기 바랍니다.",
        "투자 상품 관련해서 수익률이 매우 좋은 상품이 있어 연락드렸습니다."
    ]
    return random.choice(mock_responses)

def analyze_with_first_model(text):
    """1차 모델로 분석"""
    try:
        if not stacking_model:
            load_models()
        
        if stacking_model and tfidf_vectorizer:
            # TF-IDF 변환
            X = tfidf_vectorizer.transform([text])
            
            # 예측
            prediction = stacking_model.predict(X)[0]
            probability = stacking_model.predict_proba(X)[0]
            
            # 신뢰도 (피싱일 확률)
            confidence = probability[1] if len(probability) > 1 else 0.5
            
            return {
                'prediction': int(prediction),
                'confidence': float(confidence),
                'probabilities': probability.tolist()
            }
    except Exception as e:
        logger.error(f"1차 모델 분석 실패: {str(e)}")
    
    # 실패 시 기본값
    return {
        'prediction': random.choice([0, 1]),
        'confidence': random.uniform(0.5, 0.9),
        'probabilities': [0.5, 0.5]
    }

def analyze_with_second_model(text):
    """2차 모델로 분석 (임시 구현)"""
    # 실제로는 딥러닝 모델 사용
    return {
        'prediction': random.choice(['0', '1', '보류']),
        'confidence': random.uniform(0.6, 0.95)
    }

def generate_llm_explanation(text, prediction):
    """LLM으로 설명 생성 (임시 구현)"""
    if prediction == 1:  # 피싱
        return {
            'phishing_type': random.choice(['기관사칭형', '대출빙자형', '투자빙자형']),
            'warning': "즉시 통화를 종료하고 해당 기관에 직접 확인하시기 바랍니다.",
            'explanation': "이 대화는 보이스피싱 패턴을 보입니다. 기관명을 사칭하거나 개인정보를 요구하는 내용이 포함되어 있습니다."
        }
    else:
        return {
            'phishing_type': '정상통화',
            'warning': "정상적인 대화로 판단됩니다.",
            'explanation': "보이스피싱 의심 요소가 발견되지 않았습니다."
        }


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
        
        # 1단계: STT 처리
        try:
            transcript = vito_stt(audio_file)
        except Exception as e:
            VoicePhishingSystemLog.objects.create(
                log_nm='STT_PROCESSING_ERROR',
                ocrn_no_id=ocrn_no,
                log_reg_dt=timezone.now(),
                log_ocrn_pstn='STT_MODULE',
                err_rsn=f'STT 처리 실패: {str(e)}'
            )
            transcript = "STT 처리에 실패했습니다."
        
        # 2단계: 텍스트 전처리
        prcs_cont_1 = preprocess_text(transcript)
        prcs_cont_2 = {"processed_text": transcript}  # 2차 전처리는 임시
        
        # 3단계: 파일 정보 저장
        processed_file = ProcessdFile.objects.create(
            ocrn_no=ocrn_no,
            ocrn_hm=timezone.now(),
            trsc_file_nm=audio_file.name,
            transcript=transcript,
            prcs_cont_1=prcs_cont_1,
            prcs_cont_2=prcs_cont_2,
            vldtn_yn='Y',
            stats_file_path=f'/stats/{ocrn_no}.json',
            file_path=f'/uploads/{ocrn_no}_{audio_file.name}'
        )
        
        # 4단계: 1차 모델 분석
        first_model_result = analyze_with_first_model(transcript)
        
        # 5단계: 2차 모델 분석 (임시)
        second_model_result = analyze_with_second_model(transcript)
        
        # 6단계: LLM 설명 생성 (임시)
        llm_result = generate_llm_explanation(transcript, first_model_result['prediction'])
        
        # 7단계: 추론 결과 저장
        rslt_id = str(uuid.uuid4())
        inference_result = InferenceResult.objects.create(
            rslt_id=rslt_id,
            ocrn_no=processed_file,
            mdl_id='STACKING_V2',
            file_id=ocrn_no,
            prdt_scr=first_model_result['confidence'],
            ml_rslt_cd=str(first_model_result['prediction']),
            dl_jdgm_yn='N',  # 딥러닝 판단 여부
            phsh_tp_nm=llm_result['phishing_type'],
            warn_cn=llm_result['warning'],
            prdt_dt=timezone.now()
        )
        
        # 8단계: 기존 모델과 호환성을 위한 저장
        is_phishing = first_model_result['prediction'] == 1
        analysis_result = AnalysisResult.objects.create(
            file_name=audio_file.name,
            file_size=audio_file.size,
            file_type=audio_file.content_type,
            is_phishing=is_phishing,
            confidence=first_model_result['confidence'],
            phishing_type=llm_result['phishing_type'],
            stt_text=transcript,
            risk_factors=['기관명 언급', '계좌 관련 키워드'] if is_phishing else [],
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
            'rslt_id': rslt_id,
            'is_phishing': is_phishing,
            'confidence': first_model_result['confidence'],
            'type': llm_result['phishing_type'],
            'warning_message': llm_result['warning'],
            'explanation': llm_result['explanation'],
            'risk_factors': ['기관명 언급', '계좌 관련 키워드'] if is_phishing else [],
            'processing_time': time.time() - start_time,
            'stt_text': transcript,
            'first_model': first_model_result,
            'second_model': second_model_result,
            'file_info': {
                'name': audio_file.name,
                'size': audio_file.size,
                'type': audio_file.content_type
            }
        }
        
        return JsonResponse(result)
        
    except Exception as e:
        # 오류 로그
        try:
            VoicePhishingSystemLog.objects.create(
                log_nm='ANALYSIS_ERROR',
                ocrn_no_id=ocrn_no,
                log_reg_dt=timezone.now(),
                log_ocrn_pstn='ANALYSIS_MODULE',
                err_rsn=f'분석 중 오류 발생: {str(e)}',
                err_cd_nm='GENERAL_ERROR'
            )
        except:
            pass  # 로그 저장 실패 시에도 응답은 반환
        
        logger.error(f"Analysis error: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'error': f'분석 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def submit_feedback(request):
    """피드백 제출 API"""
    try:
        data = json.loads(request.body)
        
        rslt_id = data.get('rslt_id')
        ocrn_no = data.get('ocrn_no')
        user_prediction = data.get('user_prediction')  # 사용자가 생각하는 실제 결과
        comment = data.get('comment', '')
        
        if not all([rslt_id, ocrn_no]):
            return JsonResponse({
                'success': False,
                'error': '필수 정보가 누락되었습니다.'
            }, status=400)
        
        # 피드백 저장
        prp_no = str(uuid.uuid4())
        feedback = Feedback.objects.create(
            prp_no=prp_no,
            rslt_id=rslt_id,
            ocrn_no=ocrn_no,
            prdt_rslt_yn=user_prediction if user_prediction else 'N',
            wropn_cn=comment,
            opnn_reg_ymd=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'message': '피드백이 성공적으로 제출되었습니다.',
            'feedback_id': prp_no
        })
        
    except Exception as e:
        logger.error(f"Feedback submission error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'피드백 제출 중 오류가 발생했습니다: {str(e)}'
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
