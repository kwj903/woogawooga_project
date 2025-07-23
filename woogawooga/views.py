from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import uuid
import time
import random
from datetime import datetime

# 메인 페이지
def index(request):
    """메인 페이지 - 보이스피싱 탐지 시스템"""
    return render(request, 'voice_phishing/index.html')

# 분석 API
@csrf_exempt
@require_http_methods(["POST"])
def analyze(request):
    """음성 파일 분석 API"""
    try:
        if 'audio_file' not in request.FILES:
            return JsonResponse({'success': False, 'error': '음성 파일이 업로드되지 않았습니다.'}, status=400)
        
        uploaded_file = request.FILES['audio_file']
        
        # 파일 형식 검증
        allowed_extensions = ['.amr', '.mp3', '.wav', '.m4a']
        file_name = uploaded_file.name.lower()
        file_extension = '.' + file_name.split('.')[-1] if '.' in file_name else ''
        
        if file_extension not in allowed_extensions:
            return JsonResponse({
                'success': False,
                'error': '지원하지 않는 파일 형식입니다. AMR, MP3, WAV, M4A 파일만 업로드 가능합니다.'
            }, status=400)
        
        # 파일 크기 검증 (50MB)
        if uploaded_file.size > 50 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': '파일 크기는 50MB 이하여야 합니다.'}, status=400)
        
        # 실제 분석 로직 (여기서는 시뮬레이션)
        is_phishing = random.random() < 0.3  # 30% 확률로 피싱
        
        phishing_types = ["기관 사칭형", "대출 빙자형", "가족 사칭형", "투자 빙자형", "택배 빙자형"]
        phishing_warnings = [
            "공공기관을 사칭한 보이스피싱입니다. 즉시 통화를 종료하고 해당 기관에 직접 연락하여 확인하세요.",
            "대출 관련 보이스피싱입니다. 정식 금융기관은 전화로 개인정보를 요구하지 않습니다.",
            "가족을 사칭한 보이스피싱입니다. 가족에게 직접 연락하여 확인하고, 급하다는 이유로 돈을 요구하는 경우 절대 응하지 마세요.",
            "투자 관련 보이스피싱입니다. 고수익을 보장하는 투자는 존재하지 않습니다.",
            "택배 관련 보이스피싱입니다. 개인정보나 금융정보를 요구하는 경우 즉시 통화를 종료하세요."
        ]
        
        if is_phishing:
            phishing_type = random.choice(phishing_types)
            warning_message = random.choice(phishing_warnings)
        else:
            phishing_type = None
            warning_message = "보이스피싱 의심률이 적은 대화입니다."
        
        return JsonResponse({
            'success': True,
            'is_phishing': is_phishing,
            'type': phishing_type,
            'warning_message': warning_message,
            'confidence': random.randint(75, 95) if is_phishing else random.randint(85, 99)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'분석 중 오류가 발생했습니다: {str(e)}'}, status=500)

# 통계 페이지
def statistics(request):
    """통계 페이지"""
    # 실제로는 데이터베이스에서 통계 데이터를 조회
    # 여기서는 시뮬레이션 데이터
    total_analyses = random.randint(100, 1000)
    phishing_count = random.randint(10, total_analyses // 3)
    normal_count = total_analyses - phishing_count
    phishing_rate = (phishing_count / total_analyses * 100) if total_analyses > 0 else 0
    
    context = {
        'total_analyses': total_analyses,
        'phishing_count': phishing_count,
        'normal_count': normal_count,
        'phishing_rate': phishing_rate,
    }
    
    return render(request, 'voice_phishing/statistics.html', context)
