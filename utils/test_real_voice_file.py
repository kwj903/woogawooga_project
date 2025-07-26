#!/usr/bin/env python
"""
실제 보이스피싱 음성 파일로 전체 시스템 테스트
"""
import requests
import json
import time
import os

def test_real_voice_phishing():
    """실제 보이스피싱 파일로 테스트"""
    
    base_url = "http://127.0.0.1:8000"
    voice_file_path = "d:/workspace/금감원_보이스피싱 체험관_그놈 목소리_수사기관 사칭형/(경찰 사칭)강남서 사이버수사과입니다_.mp3"
    
    print("=" * 60)
    print("실제 보이스피싱 음성 파일 테스트 시작")
    print("=" * 60)
    print(f"파일 경로: {voice_file_path}")
    
    # 1. 파일 존재 확인
    if not os.path.exists(voice_file_path):
        print(f"[ERROR] 파일을 찾을 수 없습니다: {voice_file_path}")
        return False
    
    file_size = os.path.getsize(voice_file_path)
    print(f"파일 크기: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    
    session = requests.Session()
    
    try:
        # 2. CSRF 토큰 가져오기
        print("\n1. CSRF 토큰 가져오기...")
        response = session.get(f"{base_url}/upload/")
        if response.status_code != 200:
            print(f"[ERROR] 업로드 페이지 접근 실패: {response.status_code}")
            return False
        
        # CSRF 토큰 추출
        csrf_token = None
        if 'csrftoken' in session.cookies:
            csrf_token = session.cookies['csrftoken']
        else:
            import re
            match = re.search(r'content="([^"]+)"[^>]*name="csrf-token"', response.text)
            if match:
                csrf_token = match.group(1)
        
        if not csrf_token:
            print("[ERROR] CSRF 토큰을 찾을 수 없습니다")
            return False
        
        print(f"[OK] CSRF 토큰 획득: {csrf_token[:20]}...")
        
        # 3. 음성 파일 분석 요청
        print("\n2. 음성 파일 분석 요청...")
        start_time = time.time()
        
        with open(voice_file_path, 'rb') as f:
            files = {'audio_file': (os.path.basename(voice_file_path), f, 'audio/mpeg')}
            headers = {'X-CSRFToken': csrf_token}
            
            response = session.post(
                f"{base_url}/analyze/",
                files=files,
                headers=headers
            )
        
        analysis_time = time.time() - start_time
        print(f"분석 소요 시간: {analysis_time:.2f}초")
        print(f"응답 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[ERROR] 분석 요청 실패: {response.status_code}")
            print(f"응답 내용: {response.text[:500]}")
            return False
        
        # 4. 분석 결과 확인
        try:
            result = response.json()
            print("\n3. 분석 결과:")
            print(f"[OK] 성공: {result.get('success', False)}")
            print(f"발생번호 (ocrn_no): {result.get('ocrn_no')}")
            print(f"결과ID (rslt_id): {result.get('rslt_id')}")
            print(f"보이스피싱 여부: {result.get('is_phishing', False)}")
            print(f"신뢰도: {result.get('confidence', 0):.1%}")
            print(f"피싱 유형: {result.get('type', 'N/A')}")
            print(f"STT 결과: {result.get('stt_text', 'N/A')[:100]}...")
            print(f"경고 메시지: {result.get('warning_message', 'N/A')[:100]}...")
            
        except json.JSONDecodeError:
            print(f"[ERROR] JSON 파싱 실패: {response.text[:200]}")
            return False
        
        # 5. 피드백 제출 테스트
        print("\n4. 피드백 제출 테스트...")
        if result.get('success') and result.get('rslt_id') and result.get('ocrn_no'):
            feedback_data = {
                'rslt_id': result.get('rslt_id'),
                'ocrn_no': result.get('ocrn_no'),
                'user_prediction': 'Y',
                'comment': '실제 보이스피싱 파일로 테스트한 결과 정확합니다.'
            }
            
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'X-CSRFToken': csrf_token
            }
            
            feedback_response = session.post(
                f"{base_url}/submit_feedback/",
                data=json.dumps(feedback_data),
                headers=headers
            )
            
            print(f"피드백 응답 상태: {feedback_response.status_code}")
            
            if feedback_response.status_code == 200:
                try:
                    feedback_result = feedback_response.json()
                    if feedback_result.get('success'):
                        print("[OK] 피드백 제출 성공")
                        print(f"피드백 ID: {feedback_result.get('feedback_id')}")
                    else:
                        print(f"[ERROR] 피드백 제출 실패: {feedback_result.get('error')}")
                except json.JSONDecodeError:
                    print(f"[ERROR] 피드백 응답 JSON 파싱 실패")
            else:
                print(f"[ERROR] 피드백 제출 HTTP 오류: {feedback_response.status_code}")
                print(f"응답: {feedback_response.text[:200]}")
        
        print("\n" + "=" * 60)
        print("테스트 완료!")
        print("=" * 60)
        
        return True
        
    except requests.RequestException as e:
        print(f"[ERROR] 네트워크 오류: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_real_voice_phishing()
    if success:
        print("\n[OK] 전체 테스트 성공!")
    else:
        print("\n[ERROR] 테스트 실패")