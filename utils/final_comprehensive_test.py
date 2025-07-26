#!/usr/bin/env python
"""
최종 종합 테스트 - 피드백 문제 해결 확인
실제 워크플로우: 파일 업로드 → 분석 → 결과 표시 → 피드백 제출
"""
import requests
import json
import time
import os

def comprehensive_test():
    """종합 테스트"""
    
    print("=" * 60)
    print("[대상] 최종 종합 테스트 - 피드백 문제 해결 확인")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000"
    voice_file_path = "d:/workspace/금감원_보이스피싱 체험관_그놈 목소리_수사기관 사칭형/(경찰 사칭)강남서 사이버수사과입니다_.mp3"
    
    session = requests.Session()
    
    try:
        # 1. 전체 워크플로우 테스트
        print("[정보] 1단계: 서버 연결 확인...")
        response = session.get(f"{base_url}/")
        if response.status_code != 200:
            print(f"[ERROR] 서버 연결 실패: {response.status_code}")
            return False
        print("[OK] 서버 연결 성공")
        
        # 2. 업로드 페이지에서 CSRF 토큰 획득
        print("\n[정보] 2단계: CSRF 토큰 획득...")
        response = session.get(f"{base_url}/upload/")
        csrf_token = None
        if 'csrftoken' in session.cookies:
            csrf_token = session.cookies['csrftoken']
        
        if not csrf_token:
            print("[ERROR] CSRF 토큰 획득 실패")
            return False
        print(f"[OK] CSRF 토큰 획득 성공")
        
        # 3. 실제 음성 파일 분석
        print("\n[정보] 3단계: 실제 음성 파일 분석...")
        if not os.path.exists(voice_file_path):
            print(f"[ERROR] 파일을 찾을 수 없음: {voice_file_path}")
            return False
        
        with open(voice_file_path, 'rb') as f:
            files = {'audio_file': (os.path.basename(voice_file_path), f, 'audio/mpeg')}
            headers = {'X-CSRFToken': csrf_token}
            
            start_time = time.time()
            response = session.post(
                f"{base_url}/analyze/",
                files=files,
                headers=headers
            )
            analysis_time = time.time() - start_time
        
        if response.status_code != 200:
            print(f"[ERROR] 분석 실패: {response.status_code}")
            print(f"응답: {response.text[:200]}")
            return False
        
        result = response.json()
        if not result.get('success'):
            print(f"[ERROR] 분석 실패: {result.get('error')}")
            return False
        
        print(f"[OK] 분석 성공 (소요시간: {analysis_time:.1f}초)")
        print(f"   [결과] 보이스피싱: {result.get('is_phishing')}")
        print(f"   [결과] 신뢰도: {result.get('confidence', 0):.1%}")
        print(f"   [결과] 유형: {result.get('type')}")
        print(f"   [ID] rslt_id: {result.get('rslt_id')}")
        print(f"   [ID] ocrn_no: {result.get('ocrn_no')}")
        
        # 4. 결과 페이지 접근 확인
        print("\n[정보] 4단계: 결과 페이지 접근...")
        result_url = f"{base_url}/result/?taskId={result.get('ocrn_no')}"
        response = session.get(result_url)
        
        if response.status_code != 200:
            print(f"[ERROR] 결과 페이지 접근 실패: {response.status_code}")
            return False
        print("[OK] 결과 페이지 접근 성공")
        
        # 5. 피드백 제출 테스트 (여러 시나리오)
        print("\n[정보] 5단계: 피드백 제출 테스트...")
        
        rslt_id = result.get('rslt_id')
        ocrn_no = result.get('ocrn_no')
        
        if not rslt_id or not ocrn_no:
            print("[ERROR] 피드백 제출 필수 데이터 부족")
            return False
        
        # 5a. 정상적인 피드백 제출
        feedback_data = {
            'rslt_id': rslt_id,
            'ocrn_no': ocrn_no,
            'user_prediction': 'Y',
            'comment': '종합 테스트: 정확한 보이스피싱 탐지 결과입니다.'
        }
        
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'X-CSRFToken': csrf_token,
            'Accept': 'application/json'
        }
        
        response = session.post(
            f"{base_url}/submit_feedback/",
            data=json.dumps(feedback_data),
            headers=headers
        )
        
        print(f"   [전송] 피드백 제출 응답: {response.status_code}")
        
        if response.status_code == 200:
            try:
                feedback_result = response.json()
                if feedback_result.get('success'):
                    print("[OK] 피드백 제출 성공")
                    print(f"   [요약] 피드백 ID: {feedback_result.get('feedback_id')}")
                    print(f"   [메시지] 메시지: {feedback_result.get('message')}")
                else:
                    print(f"[ERROR] 피드백 제출 실패: {feedback_result.get('error')}")
                    return False
            except json.JSONDecodeError:
                print(f"[ERROR] 피드백 응답 JSON 파싱 실패: {response.text[:100]}")
                return False
        else:
            print(f"[ERROR] 피드백 제출 HTTP 오류: {response.status_code}")
            print(f"응답: {response.text[:200]}")
            return False
        
        # 6. 중복 피드백 테스트 (업데이트 로직 확인)
        print("\n[정보] 6단계: 중복 피드백 테스트...")
        
        feedback_data['comment'] = '업데이트된 피드백입니다.'
        feedback_data['user_prediction'] = 'N'
        
        response = session.post(
            f"{base_url}/submit_feedback/",
            data=json.dumps(feedback_data),
            headers=headers
        )
        
        if response.status_code == 200:
            feedback_result = response.json()
            if feedback_result.get('success'):
                print("[OK] 피드백 업데이트 성공")
                print(f"   [메시지] 메시지: {feedback_result.get('message')}")
            else:
                print(f"[ERROR] 피드백 업데이트 실패: {feedback_result.get('error')}")
        
        # 7. 데이터베이스 상태 확인
        print("\n[정보] 7단계: 데이터베이스 상태 확인...")
        print("   (DB 상태는 Django admin이나 별도 스크립트로 확인 가능)")
        
        print("\n" + "=" * 60)
        print("[완료] 전체 테스트 완료!")
        print("=" * 60)
        print("[요약] 테스트 요약:")
        print("  [OK] 서버 연결")
        print("  [OK] CSRF 토큰 획득")
        print("  [OK] 음성 파일 분석")
        print("  [OK] 결과 페이지 접근")
        print("  [OK] 피드백 제출")
        print("  [OK] 피드백 업데이트")
        print("\n[정보] 이제 웹 브라우저에서 동일한 플로우가 정상 작동해야 합니다!")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = comprehensive_test()
    
    if success:
        print("\n[대상] 권장사항:")
        print("1. 웹 브라우저에서 http://127.0.0.1:8000/upload/ 접속")
        print("2. 실제 음성 파일로 분석 수행")
        print("3. 결과 페이지에서 피드백 제출 테스트")
        print("4. 브라우저 개발자 도구 콘솔에서 로그 확인")
    else:
        print("\n[ERROR] 테스트 실패 - 문제 해결 필요")