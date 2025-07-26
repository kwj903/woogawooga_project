#!/usr/bin/env python
"""
Quick script to check feedback-related data
"""
import os
import sys
import django

# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from woogawooga.models import ProcessdFile, InferenceResult, Feedback

def check_recent_data():
    """최근 데이터 확인"""
    print("최근 InferenceResult 데이터:")
    recent_results = InferenceResult.objects.order_by('-prdt_dt')[:3]
    
    for result in recent_results:
        print(f"  rslt_id: {result.rslt_id}")
        print(f"  ocrn_no: {result.ocrn_no.ocrn_no if result.ocrn_no else 'None'}")
        print(f"  file_id: {result.file_id}")
        print(f"  생성시간: {result.prdt_dt}")
        print("  ---")
    
    # 특정 ID로 검색 테스트
    test_rslt_id = "64f8bb97-8b40-4c66-a5ca-daa1e4cb665e"
    test_ocrn_no = "21909908-6dc7-46c8-871d-e05cc2128cba"
    
    print(f"\n검색 테스트:")
    print(f"rslt_id '{test_rslt_id}'로 검색:")
    by_rslt = InferenceResult.objects.filter(rslt_id=test_rslt_id).first()
    if by_rslt:
        print(f"  찾음: {by_rslt.rslt_id}")
    else:
        print("  찾을 수 없음")
    
    print(f"ocrn_no '{test_ocrn_no}'로 ProcessdFile 검색:")
    by_ocrn = ProcessdFile.objects.filter(ocrn_no=test_ocrn_no).first()
    if by_ocrn:
        print(f"  찾음: {by_ocrn.ocrn_no}")
    else:
        print("  찾을 수 없음")
    
    print(f"InferenceResult에서 ocrn_no.ocrn_no '{test_ocrn_no}'로 검색:")
    by_inf_ocrn = InferenceResult.objects.filter(ocrn_no__ocrn_no=test_ocrn_no).first()
    if by_inf_ocrn:
        print(f"  찾음: {by_inf_ocrn.rslt_id}")
    else:
        print("  찾을 수 없음")

if __name__ == "__main__":
    check_recent_data()