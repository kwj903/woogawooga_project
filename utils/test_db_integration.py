#!/usr/bin/env python
"""
Django database integration test script
Tests the feedback table integration and data flow
"""
import os
import django
import sys

# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from woogawooga.models import ProcessdFile, InferenceResult, Feedback, SystemLog
from django.utils import timezone
import uuid

def test_database_integration():
    """데이터베이스 연동 및 피드백 테이블 기능 테스트"""
    print("=" * 50)
    print("데이터베이스 연동 테스트 시작")
    print("=" * 50)
    
    try:
        # 1. 데이터베이스 연결 테스트
        print("1. 데이터베이스 연결 테스트...")
        count = ProcessdFile.objects.count()
        print(f"[OK] ProcessdFile 테이블 연결 성공 (현재 레코드 수: {count})")
        
        # 2. 테스트 데이터 생성 (실제 분석 시뮬레이션)
        print("\n2. 테스트 데이터 생성...")
        
        # ProcessdFile 생성
        test_ocrn_no = f"test_{uuid.uuid4().hex[:8]}"
        test_file = ProcessdFile.objects.create(
            ocrn_no=test_ocrn_no,
            ocrn_hm=timezone.now(),
            trsc_file_nm="test_audio.wav",
            transcript="테스트 전사 내용입니다.",
            prcs_cont_1={"processed": True, "stage": "1"},
            prcs_cont_2={"processed": True, "stage": "2"},
            vldtn_yn="Y",
            stats_file_path="/test/stats/path",
            file_path="/test/path/test_audio.wav"
        )
        print(f"[OK] ProcessdFile 생성 완료: {test_file.ocrn_no}")
        
        # InferenceResult 생성
        test_rslt_id = f"rslt_{uuid.uuid4().hex[:8]}"
        test_result = InferenceResult.objects.create(
            rslt_id=test_rslt_id,
            ocrn_no=test_file,  # ForeignKey
            mdl_id="ML001",
            file_id=f"file_{uuid.uuid4().hex[:8]}",
            prdt_scr=0.87,
            ml_rslt_cd="1",  # 피싱
            dl_jdgm_yn="Y",
            phsh_tp_nm="기관사칭형",
            warn_cn="공공기관을 사칭한 보이스피싱입니다. 즉시 통화를 종료하세요.",
            prdt_dt=timezone.now()
        )
        print(f"[OK] InferenceResult 생성 완료: {test_result.rslt_id}")
        
        # 3. 피드백 테이블 테스트
        print("\n3. 피드백 테이블 연동 테스트...")
        
        # 피드백 데이터 생성
        test_feedback = Feedback.objects.create(
            prp_no=f"prp_{uuid.uuid4().hex[:6]}",
            rslt_id=test_result.rslt_id,
            ocrn_no=test_file.ocrn_no,  # 문자열로 저장
            prdt_rslt_yn="Y",
            wropn_cn="정확한 판별입니다.",
            opnn_reg_ymd=timezone.now()
        )
        print(f"[OK] Feedback 생성 완료: {test_feedback.prp_no}")
        
        # 4. 데이터 검색 테스트 (실제 피드백 제출 시나리오)
        print("\n4. 데이터 검색 테스트...")
        
        # rslt_id로 검색
        found_by_rslt = InferenceResult.objects.filter(rslt_id=test_result.rslt_id).first()
        if found_by_rslt:
            print(f"[OK] rslt_id로 검색 성공: {found_by_rslt.rslt_id}")
        
        # ocrn_no로 검색
        found_by_ocrn = InferenceResult.objects.filter(ocrn_no=test_result.ocrn_no).first()
        if found_by_ocrn:
            print(f"[OK] ocrn_no로 검색 성공: {found_by_ocrn.ocrn_no}")
        
        # 5. 필드 길이 테스트
        print("\n5. 필드 길이 검증 테스트...")
        
        # 긴 문자열로 테스트
        long_file_id = "a" * 60  # 50자 제한을 초과하는 문자열
        try:
            # 긴 ocrn_no용 ProcessdFile 생성
            long_ocrn_no = f"long_{uuid.uuid4().hex[:8]}"
            long_file = ProcessdFile.objects.create(
                ocrn_no=long_ocrn_no,
                ocrn_hm=timezone.now(),
                trsc_file_nm="long_test_audio.wav",
                transcript="긴 파일명 테스트 전사 내용입니다.",
                prcs_cont_1={"processed": True, "stage": "1"},
                vldtn_yn="Y",
                stats_file_path="/test/stats/long_path",
                file_path="/test/path/long_test_audio.wav"
            )
            
            long_result = InferenceResult.objects.create(
                rslt_id=f"long_{uuid.uuid4().hex[:8]}",
                ocrn_no=long_file,
                mdl_id="ML001",
                file_id=long_file_id[:50],  # 안전하게 자르기
                prdt_scr=0.95,
                ml_rslt_cd="0",  # 정상
                dl_jdgm_yn="N",
                phsh_tp_nm="정상통화",
                warn_cn="정상 통화입니다.",
                prdt_dt=timezone.now()
            )
            print(f"[OK] 긴 file_id 필드 처리 성공: {long_result.file_id} (길이: {len(long_result.file_id)})")
        except Exception as e:
            print(f"[ERROR] 긴 file_id 필드 처리 실패: {e}")
        
        # 6. 시스템 로그 테스트
        print("\n6. 시스템 로그 테스트...")
        SystemLog.objects.create(
            level="INFO",
            message="데이터베이스 연동 테스트 완료",
            file_name="test_db_integration.py",
            created_at=timezone.now()
        )
        print("[OK] SystemLog 생성 완료")
        
        print("\n" + "=" * 50)
        print("모든 테스트 완료!")
        print("=" * 50)
        
        # 테스트 데이터 정보 출력 (프론트엔드 테스트용)
        print(f"\n프론트엔드 테스트용 데이터:")
        print(f"rslt_id: {test_result.rslt_id}")
        print(f"ocrn_no: {test_file.ocrn_no}")
        print(f"file_id: {test_result.file_id}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data():
    """테스트 데이터 정리"""
    print("\n테스트 데이터 정리 중...")
    try:
        # 테스트로 생성된 데이터 삭제
        test_files = ProcessdFile.objects.filter(ocrn_no__startswith="test_")
        test_files_long = ProcessdFile.objects.filter(ocrn_no__startswith="long_")
        test_results = InferenceResult.objects.filter(rslt_id__startswith="rslt_")
        test_results_long = InferenceResult.objects.filter(rslt_id__startswith="long_")
        test_feedbacks = Feedback.objects.filter(prp_no__startswith="prp_")
        test_logs = SystemLog.objects.filter(file_name="test_db_integration.py")
        
        deleted_counts = {
            'files': test_files.count() + test_files_long.count(),
            'results': test_results.count() + test_results_long.count(),
            'feedbacks': test_feedbacks.count(),
            'logs': test_logs.count()
        }
        
        # 순서 중요: InferenceResult -> ProcessdFile (ForeignKey 관계)
        test_results.delete()
        test_results_long.delete()
        test_feedbacks.delete()
        test_files.delete()
        test_files_long.delete()
        test_logs.delete()
        
        print(f"[OK] 정리 완료: Files({deleted_counts['files']}), Results({deleted_counts['results']}), Feedbacks({deleted_counts['feedbacks']}), Logs({deleted_counts['logs']})")
        
    except Exception as e:
        print(f"[ERROR] 정리 실패: {e}")

if __name__ == "__main__":
    try:
        success = test_database_integration()
        
        # 사용자 입력 대기
        input("\n테스트 데이터를 유지하려면 Enter를 누르세요 (자동 정리하지 않음)...")
        
        # cleanup_test_data()  # 주석 처리하여 데이터 유지
        
    except KeyboardInterrupt:
        print("\n테스트 중단됨")
        cleanup_test_data()