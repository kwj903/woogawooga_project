#!/usr/bin/env python
"""
최근 웹페이지 활동의 데이터베이스 저장 상태 확인 스크립트
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from woogawooga.models import ProcessdFile, InferenceResult, Feedback, SystemLog

def check_recent_activity():
    """최근 웹페이지 활동 확인"""
    
    print("=" * 70)
    print("[검사] 최근 웹페이지 활동의 데이터베이스 저장 상태 확인")
    print("=" * 70)
    
    # 최근 1시간 내 활동 기준
    one_hour_ago = timezone.now() - timedelta(hours=1)
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"검사 기준 시간: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"오늘 0시 이후: {today_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"최근 1시간: {one_hour_ago.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. ProcessdFile (업로드된 파일) 확인
    print("\n" + "=" * 50)
    print("[1단계] 업로드된 음성 파일 확인 (ProcessdFile)")
    print("=" * 50)
    
    recent_files = ProcessdFile.objects.filter(ocrn_hm__gte=today_start).order_by('-ocrn_hm')[:5]
    
    if recent_files:
        print(f"오늘 업로드된 파일: {recent_files.count()}개")
        for i, file_obj in enumerate(recent_files, 1):
            print(f"\n[파일 {i}]")
            print(f"  발생번호 (ocrn_no): {file_obj.ocrn_no}")
            print(f"  파일명: {file_obj.trsc_file_nm}")
            print(f"  업로드 시간: {file_obj.ocrn_hm.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  전사 내용: {file_obj.transcript[:100] if file_obj.transcript else 'None'}...")
            print(f"  검증 여부: {file_obj.vldtn_yn}")
            print(f"  파일 경로: {file_obj.file_path}")
    else:
        print("[정보] 오늘 업로드된 파일이 없습니다.")
    
    # 2. InferenceResult (분석 결과) 확인
    print("\n" + "=" * 50)
    print("[2단계] 보이스피싱 분석 결과 확인 (InferenceResult)")
    print("=" * 50)
    
    recent_results = InferenceResult.objects.filter(prdt_dt__gte=today_start).order_by('-prdt_dt')[:5]
    
    if recent_results:
        print(f"오늘 생성된 분석 결과: {recent_results.count()}개")
        for i, result in enumerate(recent_results, 1):
            print(f"\n[분석 {i}]")
            print(f"  결과ID (rslt_id): {result.rslt_id}")
            print(f"  발생번호 (ocrn_no): {result.ocrn_no.ocrn_no if result.ocrn_no else 'None'}")
            print(f"  파일ID: {result.file_id}")
            print(f"  분석 시간: {result.prdt_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  예측 점수: {result.prdt_scr}")
            print(f"  ML 결과: {result.ml_rslt_cd} ({'보이스피싱' if result.ml_rslt_cd == '1' else '정상'})")
            print(f"  DL 판단: {result.dl_jdgm_yn}")
            print(f"  피싱 유형: {result.phsh_tp_nm}")
            print(f"  경고 내용: {result.warn_cn[:100] if result.warn_cn else 'None'}...")
    else:
        print("[정보] 오늘 생성된 분석 결과가 없습니다.")
    
    # 3. Feedback (사용자 피드백) 확인
    print("\n" + "=" * 50)
    print("[3단계] 사용자 피드백 확인 (Feedback)")
    print("=" * 50)
    
    recent_feedbacks = Feedback.objects.filter(opnn_reg_ymd__gte=today_start).order_by('-opnn_reg_ymd')[:5]
    
    if recent_feedbacks:
        print(f"오늘 제출된 피드백: {recent_feedbacks.count()}개")
        for i, feedback in enumerate(recent_feedbacks, 1):
            print(f"\n[피드백 {i}]")
            print(f"  제안번호 (prp_no): {feedback.prp_no}")
            print(f"  결과ID (rslt_id): {feedback.rslt_id}")
            print(f"  발생번호 (ocrn_no): {feedback.ocrn_no}")
            print(f"  사용자 예측: {feedback.prdt_rslt_yn} ({'정확' if feedback.prdt_rslt_yn == 'Y' else '부정확'})")
            print(f"  의견 내용: {feedback.wropn_cn[:100] if feedback.wropn_cn else 'None'}...")
            print(f"  등록 시간: {feedback.opnn_reg_ymd.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("[정보] 오늘 제출된 피드백이 없습니다.")
    
    # 4. SystemLog (시스템 로그) 확인
    print("\n" + "=" * 50)
    print("[4단계] 시스템 로그 확인 (SystemLog)")
    print("=" * 50)
    
    recent_logs = SystemLog.objects.filter(created_at__gte=today_start).order_by('-created_at')[:10]
    
    if recent_logs:
        print(f"오늘 생성된 시스템 로그: {recent_logs.count()}개")
        for i, log in enumerate(recent_logs, 1):
            print(f"\n[로그 {i}]")
            print(f"  로그 레벨: {log.level}")
            print(f"  메시지: {log.message[:100]}...")
            print(f"  파일명: {log.file_name}")
            print(f"  생성 시간: {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("[정보] 오늘 생성된 시스템 로그가 없습니다.")
    
    # 5. 데이터 연관성 확인
    print("\n" + "=" * 50)
    print("[5단계] 데이터 연관성 확인")
    print("=" * 50)
    
    if recent_results:
        latest_result = recent_results[0]
        print(f"\n가장 최근 분석 결과: {latest_result.rslt_id}")
        
        # 연관된 파일 확인
        if latest_result.ocrn_no:
            print(f"  -> 연관 파일: {latest_result.ocrn_no.trsc_file_nm}")
            print(f"  -> 파일 경로: {latest_result.ocrn_no.file_path}")
        
        # 연관된 피드백 확인
        related_feedback = Feedback.objects.filter(rslt_id=latest_result.rslt_id).first()
        if related_feedback:
            print(f"  -> 연관 피드백: {related_feedback.prp_no}")
            print(f"  -> 피드백 내용: {related_feedback.wropn_cn[:50]}...")
            print(f"  -> 사용자 평가: {'정확' if related_feedback.prdt_rslt_yn == 'Y' else '부정확'}")
        else:
            print("  -> 연관 피드백: 없음")
    
    # 6. 최근 1시간 내 활동 요약
    print("\n" + "=" * 50)
    print("[6단계] 최근 1시간 내 활동 요약")
    print("=" * 50)
    
    hour_files = ProcessdFile.objects.filter(ocrn_hm__gte=one_hour_ago).count()
    hour_results = InferenceResult.objects.filter(prdt_dt__gte=one_hour_ago).count()
    hour_feedbacks = Feedback.objects.filter(opnn_reg_ymd__gte=one_hour_ago).count()
    hour_logs = SystemLog.objects.filter(created_at__gte=one_hour_ago).count()
    
    print(f"최근 1시간 내:")
    print(f"  📁 업로드된 파일: {hour_files}개")
    print(f"  🔍 분석 결과: {hour_results}개")
    print(f"  💬 사용자 피드백: {hour_feedbacks}개")
    print(f"  📋 시스템 로그: {hour_logs}개")
    
    if hour_files > 0 or hour_results > 0 or hour_feedbacks > 0:
        print("\n[OK] 최근 활동이 데이터베이스에 정상적으로 기록되고 있습니다!")
    else:
        print("\n[INFO] 최근 1시간 내 활동이 없습니다.")
    
    print("\n" + "=" * 70)
    print("데이터베이스 저장 상태 확인 완료!")
    print("=" * 70)

if __name__ == "__main__":
    check_recent_activity()