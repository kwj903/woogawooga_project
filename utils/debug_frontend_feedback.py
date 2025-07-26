#!/usr/bin/env python
"""
프론트엔드 피드백 제출 문제 디버깅
실제 웹 브라우저와 같은 환경에서 테스트
"""
import requests
import json
import time

def debug_frontend_feedback():
    """프론트엔드 피드백 제출 디버깅"""
    
    print("=" * 60)
    print("프론트엔드 피드백 제출 문제 디버깅")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000"
    session = requests.Session()
    
    try:
        # 1. 홈페이지 접근 (실제 사용자 흐름)
        print("1. 홈페이지 접근...")
        response = session.get(f"{base_url}/")
        print(f"홈페이지 상태: {response.status_code}")
        
        # 2. 업로드 페이지 접근
        print("\n2. 업로드 페이지 접근...")
        response = session.get(f"{base_url}/upload/")
        print(f"업로드 페이지 상태: {response.status_code}")
        
        # CSRF 토큰 추출
        csrf_token = None
        if 'csrftoken' in session.cookies:
            csrf_token = session.cookies['csrftoken']
        
        print(f"CSRF 토큰: {csrf_token[:20] if csrf_token else 'None'}...")
        
        # 3. 가짜 분석 요청 (간단한 더미 파일)
        print("\n3. 분석 요청...")
        dummy_audio = b'RIFF' + b'\x00' * 1000  # 더미 오디오 데이터
        
        files = {'audio_file': ('test.wav', dummy_audio, 'audio/wav')}
        headers = {'X-CSRFToken': csrf_token}
        
        response = session.post(
            f"{base_url}/analyze/",
            files=files,
            headers=headers
        )
        
        print(f"분석 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"분석 성공: {result.get('success')}")
            rslt_id = result.get('rslt_id')
            ocrn_no = result.get('ocrn_no')
            print(f"rslt_id: {rslt_id}")
            print(f"ocrn_no: {ocrn_no}")
            
            # 4. 결과 페이지 접근 (실제 사용자 흐름)
            print(f"\n4. 결과 페이지 접근...")
            response = session.get(f"{base_url}/result/?taskId={ocrn_no}")
            print(f"결과 페이지 상태: {response.status_code}")
            
            # 5. 피드백 제출 (여러 방법으로 테스트)
            print(f"\n5. 피드백 제출 테스트...")
            
            feedback_data = {
                'rslt_id': rslt_id,
                'ocrn_no': ocrn_no,
                'user_prediction': 'Y',
                'comment': '정확한 분석입니다'
            }
            
            # 5a. JSON 형태로 제출 (현재 프론트엔드 방식)
            print("5a. JSON 방식 피드백 제출...")
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
            
            print(f"JSON 피드백 응답 상태: {response.status_code}")
            print(f"응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"JSON 피드백 결과: {result}")
                except json.JSONDecodeError:
                    print(f"JSON 파싱 실패. 응답 내용: {response.text[:200]}")
            else:
                print(f"오류 응답: {response.text[:300]}")
            
            # 5b. 폼 데이터 방식으로 제출
            print("\n5b. 폼 데이터 방식 피드백 제출...")
            headers = {
                'X-CSRFToken': csrf_token,
                'Accept': 'application/json'
            }
            
            response = session.post(
                f"{base_url}/submit_feedback/",
                data=feedback_data,
                headers=headers
            )
            
            print(f"폼 데이터 피드백 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"폼 데이터 피드백 결과: {result}")
                except json.JSONDecodeError:
                    print(f"JSON 파싱 실패. 응답 내용: {response.text[:200]}")
            else:
                print(f"오류 응답: {response.text[:300]}")
            
            # 6. 쿠키 및 세션 상태 확인
            print(f"\n6. 세션 상태 확인...")
            print(f"쿠키: {dict(session.cookies)}")
            
        else:
            print(f"분석 실패: {response.text[:200]}")
            
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

def test_direct_feedback():
    """직접 피드백 API 테스트"""
    print("\n" + "=" * 60)
    print("직접 피드백 API 테스트")
    print("=" * 60)
    
    # 최근 분석 결과 데이터 사용
    feedback_data = {
        'rslt_id': 'b15743d3-4ec1-4a5b-8811-e78c394f8177',
        'ocrn_no': 'e8daec74-8ddc-4795-8f1b-0d893c1bdb71',
        'user_prediction': 'Y',
        'comment': '브라우저 테스트 피드백'
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/submit_feedback/",
            json=feedback_data,
            headers={
                'Content-Type': 'application/json; charset=utf-8',
                'Accept': 'application/json'
            }
        )
        
        print(f"직접 테스트 응답 상태: {response.status_code}")
        print(f"응답 내용: {response.text}")
        
    except Exception as e:
        print(f"직접 테스트 오류: {e}")

if __name__ == "__main__":
    debug_frontend_feedback()
    test_direct_feedback()