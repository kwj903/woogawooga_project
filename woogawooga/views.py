from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import uuid
import time
import random
from datetime import datetime

# 메인 페이지 (index.html)
def index(request):
    """메인 페이지 - 보이스피싱 탐지 시스템 소개"""
    return render(request, 'index.html')

# 업로드 페이지 (upload.html)
def upload(request):
    """파일 업로드 페이지"""
    return render(request, 'upload.html')

# 분석 페이지 (analysis.html)
def analysis(request):
    """분석 진행 페이지"""
    task_id = request.GET.get('taskId', None)
    context = {
        'task_id': task_id
    }
    return render(request, 'analysis.html', context)

def analysis_detail(request, task_id):
    """특정 Task ID의 분석 페이지"""
    context = {
        'task_id': task_id
    }
    return render(request, 'analysis.html', context)

# 결과 페이지 (result.html)
def result(request):
    """분석 결과 페이지"""
    task_id = request.GET.get('taskId', None)
    context = {
        'task_id': task_id
    }
    return render(request, 'result.html', context)

def result_detail(request, task_id):
    """특정 Task ID의 결과 페이지"""
    context = {
        'task_id': task_id
    }
    return render(request, 'result.html', context)

# API 엔드포인트들

@csrf_exempt
@require_http_methods(["POST"])
def api_upload(request):
    """파일 업로드 API"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': '파일이 업로드되지 않았습니다.'}, status=400)
        
        uploaded_file = request.FILES['file']
        
        # 파일 형식 검증
        allowed_extensions = ['.amr', '.mp3', '.wav']
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        if f'.{file_extension}' not in allowed_extensions:
            return JsonResponse({
                'error': '지원하지 않는 파일 형식입니다. AMR, MP3, WAV 파일만 업로드 가능합니다.'
            }, status=400)
        
        # 파일 크기 검증 (50MB)
        if uploaded_file.size > 50 * 1024 * 1024:
            return JsonResponse({'error': '파일 크기는 50MB 이하여야 합니다.'}, status=400)
        
        # 파일 정보 반환
        file_info = {
            'name': uploaded_file.name,
            'size': uploaded_file.size,
            'type': uploaded_file.content_type,
            'upload_time': datetime.now().isoformat()
        }
        
        return JsonResponse({
            'success': True,
            'message': '파일이 성공적으로 업로드되었습니다.',
            'file_info': file_info
        })
        
    except Exception as e:
        return JsonResponse({'error': f'업로드 중 오류가 발생했습니다: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_start_analysis(request):
    """분석 시작 API"""
    try:
        data = json.loads(request.body)
        
        # Task ID 생성
        task_id = f"TASK-{int(time.time())}-{str(uuid.uuid4())[:8]}"
        
        # 분석 시작 로그 (실제로는 백그라운드 작업으로 처리)
        print(f"분석 시작: Task ID {task_id}")
        
        return JsonResponse({
            'success': True,
            'task_id': task_id,
            'message': '분석이 시작되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'분석 시작 중 오류가 발생했습니다: {str(e)}'}, status=500)

def api_analysis_status(request, task_id):
    """분석 상태 확인 API"""
    try:
        # 실제로는 데이터베이스나 캐시에서 상태를 조회
        # 여기서는 시뮬레이션 데이터 반환
        
        # 랜덤한 진행 상태 시뮬레이션
        status_options = ['stt', 'ml', 'dl', 'completed']
        current_status = random.choice(status_options)
        
        if current_status == 'completed':
            return JsonResponse({
                'status': 'completed',
                'task_id': task_id,
                'redirect_url': f'/result/{task_id}/'
            })
        else:
            progress = random.randint(10, 90)
            return JsonResponse({
                'status': 'processing',
                'current_step': current_status,
                'progress': progress,
                'task_id': task_id
            })
            
    except Exception as e:
        return JsonResponse({'error': f'상태 확인 중 오류가 발생했습니다: {str(e)}'}, status=500)

def api_result(request, task_id):
    """분석 결과 API"""
    try:
        # 실제로는 데이터베이스에서 결과를 조회
        # 여기서는 시뮬레이션 데이터 반환
        
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
            warning = random.choice(phishing_warnings)
            confidence = random.randint(75, 95)
        else:
            phishing_type = "정상 통화"
            warning = "이 통화는 정상으로 판별되었습니다. 하지만 항상 개인정보 보호에 주의하시고, 의심스러운 요청이 있을 때는 직접 해당 기관에 확인하시기 바랍니다."
            confidence = random.randint(85, 99)
        
        result_data = {
            'task_id': task_id,
            'verdict': 'phishing' if is_phishing else 'normal',
            'type': phishing_type,
            'confidence': confidence,
            'warning': warning,
            'analysis_stage': '1차 ML + 2차 DL' if random.random() > 0.3 else '1차 ML',
            'completed_at': datetime.now().isoformat()
        }
        
        return JsonResponse({
            'success': True,
            'result': result_data
        })
        
    except Exception as e:
        return JsonResponse({'error': f'결과 조회 중 오류가 발생했습니다: {str(e)}'}, status=500)
