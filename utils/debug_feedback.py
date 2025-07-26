#!/usr/bin/env python
"""
Debug feedback submission
"""
import os
import sys
import django
import json

# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from woogawooga.models import ProcessdFile, InferenceResult, Feedback
from django.utils import timezone
from woogawooga.views import generate_short_id

def debug_feedback_submission():
    """피드백 제출 디버깅"""
    
    # 테스트 데이터
    rslt_id = "64f8bb97-8b40-4c66-a5ca-daa1e4cb665e"
    ocrn_no = "21909908-6dc7-46c8-871d-e05cc2128cba"
    user_prediction = "Y"
    comment = "테스트 피드백입니다."
    
    print(f"디버깅 시작:")
    print(f"  rslt_id: {rslt_id}")
    print(f"  ocrn_no: {ocrn_no}")
    
    try:
        # 1. 데이터 검색
        print("\n1. 데이터 검색...")
        inference_result = InferenceResult.objects.filter(rslt_id=rslt_id).first()
        
        if inference_result:
            print(f"  InferenceResult 찾음: {inference_result.rslt_id}")
            print(f"  연결된 ocrn_no: {inference_result.ocrn_no.ocrn_no}")
            print(f"  연결된 파일명: {inference_result.ocrn_no.trsc_file_nm}")
        else:
            print("  InferenceResult를 찾을 수 없음")
            return
        
        # 2. 중복 피드백 확인
        print("\n2. 중복 피드백 확인...")
        existing_feedback = Feedback.objects.filter(
            rslt_id=rslt_id,
            ocrn_no=ocrn_no
        ).first()
        
        if existing_feedback:
            print(f"  기존 피드백 존재: {existing_feedback.prp_no}")
        else:
            print("  새 피드백 생성 필요")
        
        # 3. 피드백 생성 시도
        print("\n3. 피드백 생성 시도...")
        prp_no = generate_short_id()
        print(f"  생성된 prp_no: {prp_no} (길이: {len(prp_no)})")
        
        # 필드 길이 검증
        print("\n4. 필드 길이 검증...")
        print(f"  prp_no: {len(prp_no)} <= 20? {len(prp_no) <= 20}")
        print(f"  rslt_id: {len(rslt_id)} <= 50? {len(rslt_id) <= 50}")
        print(f"  ocrn_no: {len(ocrn_no)} <= 50? {len(ocrn_no) <= 50}")
        print(f"  comment: {len(comment)} <= 1000? {len(comment) <= 1000}")
        
        # 실제 피드백 생성
        print("\n5. 피드백 생성...")
        feedback = Feedback.objects.create(
            prp_no=prp_no,
            rslt_id=rslt_id,
            ocrn_no=ocrn_no,
            prdt_rslt_yn=user_prediction,
            wropn_cn=comment,
            opnn_reg_ymd=timezone.now()
        )
        
        print(f"  피드백 생성 성공: {feedback.prp_no}")
        print(f"  저장된 내용: {feedback.wropn_cn}")
        
        return True
        
    except Exception as e:
        print(f"\n오류 발생: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_feedback_submission()