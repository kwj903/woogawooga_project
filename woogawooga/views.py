from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import AnalysisResult, SystemLog
import json
import time
import random
import logging

# 로거 설정
logger = logging.getLogger(__name__)


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
    
    try:
        # 업로드된 파일 확인
        if 'audio_file' not in request.FILES:
            SystemLog.objects.create(
                level='WARNING',
                message='오디오 파일이 업로드되지 않음',
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
                level='WARNING',
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
                level='WARNING',
                message=f'파일 크기 초과: {audio_file.size} bytes',
                file_name=audio_file.name,
                ip_address=client_ip
            )
            return JsonResponse({
                'success': False,
                'error': '파일 크기가 너무 큽니다. 최대 50MB까지 지원합니다.'
            }, status=400)
        
        # 실제 분석 로직 (현재는 모의 데이터)
        # TODO: 실제 VITO STT API, ML 모델, DL 모델, LLM 연동
        
        # 모의 분석 결과 생성
        is_phishing = random.choice([True, False])
        confidence = random.uniform(0.7, 0.95)
        
        if is_phishing:
            phishing_types = ['기관사칭형', '대출빙자형', '투자빙자형', '기타']
            phishing_type = random.choice(phishing_types)
            risk_factors = ['기관명 언급', '계좌 관련 키워드', '긴급성 표현', '개인정보 요구']
            warning_message = "즉시 통화를 종료하고 해당 기관에 직접 확인하시기 바랍니다."
            explanation = "이 대화는 전형적인 기관사칭 보이스피싱 패턴을 보입니다."
            stt_text = "안녕하세요. 저는 금융감독원에서 나온 김철수입니다. 고객님의 계좌에 이상 거래가 발견되어 연락드렸습니다."
        else:
            phishing_type = None
            risk_factors = []
            warning_message = "보이스피싱 의심률이 적은 대화입니다."
            explanation = "정상적인 대화로 판단됩니다."
            stt_text = "안녕하세요. 고객님께서 문의하신 상품에 대해 안내드리겠습니다."
        
        # 처리 시간 계산
        processing_time = time.time() - start_time
        
        # 분석 결과 데이터베이스에 저장
        analysis_result = AnalysisResult.objects.create(
            file_name=audio_file.name,
            file_size=audio_file.size,
            file_type=audio_file.content_type,
            is_phishing=is_phishing,
            confidence=confidence,
            phishing_type=phishing_type,
            stt_text=stt_text,
            risk_factors=risk_factors,
            explanation=explanation,
            warning_message=warning_message,
            processing_time=processing_time,
            ip_address=client_ip
        )
        
        # 성공 로그
        SystemLog.objects.create(
            level='INFO',
            message=f'분석 완료: {audio_file.name} - {"피싱" if is_phishing else "정상"}',
            file_name=audio_file.name,
            ip_address=client_ip
        )
        
        # 분석 결과 반환
        result = {
            'success': True,
            'is_phishing': is_phishing,
            'confidence': confidence,
            'type': phishing_type,
            'warning_message': warning_message,
            'explanation': explanation,
            'risk_factors': risk_factors,
            'processing_time': processing_time,
            'stt_text': stt_text,
            'file_info': {
                'name': audio_file.name,
                'size': audio_file.size,
                'type': audio_file.content_type
            }
        }
        
        return JsonResponse(result)
        
    except Exception as e:
        # 오류 로그
        SystemLog.objects.create(
            level='ERROR',
            message=f'분석 중 오류 발생: {str(e)}',
            file_name=audio_file.name if 'audio_file' in locals() else None,
            ip_address=client_ip
        )
        
        logger.error(f"Analysis error: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'error': f'분석 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


def statistics(request):
    """통계 페이지"""
    total_analyses = AnalysisResult.objects.count()
    phishing_count = AnalysisResult.objects.filter(is_phishing=True).count()
    normal_count = AnalysisResult.objects.filter(is_phishing=False).count()
    
    context = {
        'total_analyses': total_analyses,
        'phishing_count': phishing_count,
        'normal_count': normal_count,
        'phishing_rate': (phishing_count / total_analyses * 100) if total_analyses > 0 else 0,
    }
    
    return render(request, 'voice_phishing/statistics.html', context)
