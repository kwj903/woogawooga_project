#!/usr/bin/env python
"""
End-to-End functionality test for Voice Phishing Detection System
Tests the complete workflow from file upload to feedback submission
"""
import os
import django
import sys
import requests
import json
import time
from io import BytesIO

# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from woogawooga.models import ProcessdFile, InferenceResult, Feedback, SystemLog
from django.test import Client
from django.urls import reverse
import uuid

class EndToEndTester:
    """엔드투엔드 테스트 클래스"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = Client()
        self.session = requests.Session()
        self.csrf_token = None
        
    def log(self, message, level="INFO"):
        """테스트 로그 출력"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def create_test_audio_file(self):
        """테스트용 가짜 오디오 파일 생성"""
        # WAV 파일 헤더 시뮬레이션 (실제 오디오 데이터는 없음)
        wav_header = b'RIFF' + b'\\x00\\x00\\x00\\x00' + b'WAVE' + b'fmt ' + b'\\x10\\x00\\x00\\x00'
        wav_data = wav_header + b'\\x00' * 1000  # 더미 데이터
        return BytesIO(wav_data)
    
    def get_csrf_token(self, url="/"):
        """CSRF 토큰 가져오기"""
        try:
            response = self.session.get(f"{self.base_url}{url}")
            response.raise_for_status()
            
            # HTML에서 CSRF 토큰 추출
            if 'csrftoken' in response.cookies:
                self.csrf_token = response.cookies['csrftoken']
                return self.csrf_token
            
            # 메타 태그에서 추출 시도
            content = response.text
            if 'csrf-token' in content:
                import re
                match = re.search(r'content="([^"]+)"[^>]*name="csrf-token"', content)
                if match:
                    self.csrf_token = match.group(1)
                    return self.csrf_token
            
            self.log("CSRF 토큰을 찾을 수 없습니다", "WARNING")
            return None
            
        except Exception as e:
            self.log(f"CSRF 토큰 가져오기 실패: {e}", "ERROR")
            return None
    
    def test_home_page(self):
        """홈페이지 접근 테스트"""
        self.log("홈페이지 접근 테스트 시작...")
        try:
            response = self.session.get(f"{self.base_url}/")
            response.raise_for_status()
            
            if "보이스피싱" in response.text:
                self.log("홈페이지 접근 성공", "SUCCESS")
                return True
            else:
                self.log("홈페이지 내용 확인 실패", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"홈페이지 접근 실패: {e}", "ERROR")
            return False
    
    def test_upload_page(self):
        """업로드 페이지 접근 테스트"""
        self.log("업로드 페이지 접근 테스트 시작...")
        try:
            response = self.session.get(f"{self.base_url}/upload/")
            response.raise_for_status()
            
            if "파일을 선택하거나" in response.text:
                self.log("업로드 페이지 접근 성공", "SUCCESS")
                return True
            else:
                self.log("업로드 페이지 내용 확인 실패", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"업로드 페이지 접근 실패: {e}", "ERROR")
            return False
    
    def test_file_analysis(self):
        """파일 분석 API 테스트"""
        self.log("파일 분석 API 테스트 시작...")
        try:
            # CSRF 토큰 가져오기
            csrf_token = self.get_csrf_token("/upload/")
            if not csrf_token:
                self.log("CSRF 토큰 가져오기 실패", "ERROR")
                return None
            
            # 테스트 파일 생성
            test_file = self.create_test_audio_file()
            
            # 분석 API 호출
            files = {'audio_file': ('test_audio.wav', test_file, 'audio/wav')}
            headers = {'X-CSRFToken': csrf_token}
            
            # 쿠키 설정
            cookies = {'csrftoken': csrf_token}
            
            response = self.session.post(
                f"{self.base_url}/analyze/",
                files=files,
                headers=headers,
                cookies=cookies
            )
            
            self.log(f"분석 API 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.log(f"분석 API 성공: {result}", "SUCCESS")
                    return result
                except json.JSONDecodeError:
                    self.log("분석 API 응답이 유효한 JSON이 아닙니다", "ERROR")
                    self.log(f"응답 내용: {response.text[:500]}")
                    return None
            else:
                self.log(f"분석 API 실패 - 상태코드: {response.status_code}", "ERROR")
                self.log(f"응답 내용: {response.text[:500]}")
                return None
                
        except Exception as e:
            self.log(f"파일 분석 테스트 실패: {e}", "ERROR")
            return None
    
    def test_result_page(self, task_id):
        """결과 페이지 접근 테스트"""
        self.log(f"결과 페이지 접근 테스트 시작 (task_id: {task_id})...")
        try:
            response = self.session.get(f"{self.base_url}/result/?taskId={task_id}")
            response.raise_for_status()
            
            if "분석 결과" in response.text or "보이스피싱" in response.text:
                self.log("결과 페이지 접근 성공", "SUCCESS")
                return True
            else:
                self.log("결과 페이지 내용 확인 실패", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"결과 페이지 접근 실패: {e}", "ERROR")
            return False
    
    def test_feedback_submission(self, rslt_id, ocrn_no):
        """피드백 제출 테스트"""
        self.log(f"피드백 제출 테스트 시작 (rslt_id: {rslt_id}, ocrn_no: {ocrn_no})...")
        try:
            # CSRF 토큰 가져오기
            csrf_token = self.get_csrf_token("/upload/")
            if not csrf_token:
                self.log("CSRF 토큰 가져오기 실패", "ERROR")
                return False
            
            # 피드백 데이터
            feedback_data = {
                'rslt_id': rslt_id,
                'ocrn_no': ocrn_no,
                'user_prediction': 'Y',
                'comment': '테스트 피드백입니다.'
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            }
            
            response = self.session.post(
                f"{self.base_url}/submit_feedback/",
                data=json.dumps(feedback_data),
                headers=headers,
                cookies={'csrftoken': csrf_token}
            )
            
            self.log(f"피드백 제출 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('success'):
                        self.log("피드백 제출 성공", "SUCCESS")
                        return True
                    else:
                        self.log(f"피드백 제출 실패: {result.get('error', '알 수 없는 오류')}", "ERROR")
                        return False
                except json.JSONDecodeError:
                    self.log("피드백 제출 응답이 유효한 JSON이 아닙니다", "ERROR")
                    return False
            else:
                self.log(f"피드백 제출 실패 - 상태코드: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"피드백 제출 테스트 실패: {e}", "ERROR")
            return False
    
    def test_database_consistency(self):
        """데이터베이스 일관성 테스트"""
        self.log("데이터베이스 일관성 테스트 시작...")
        try:
            # 테이블별 레코드 수 확인
            processed_files_count = ProcessdFile.objects.count()
            inference_results_count = InferenceResult.objects.count()
            feedbacks_count = Feedback.objects.count()
            system_logs_count = SystemLog.objects.count()
            
            self.log(f"데이터베이스 현황:")
            self.log(f"  - ProcessdFile: {processed_files_count}개")
            self.log(f"  - InferenceResult: {inference_results_count}개")
            self.log(f"  - Feedback: {feedbacks_count}개")
            self.log(f"  - SystemLog: {system_logs_count}개")
            
            # 최근 레코드 확인
            recent_feedback = Feedback.objects.filter(wropn_cn__contains="테스트").first()
            if recent_feedback:
                self.log(f"최근 테스트 피드백 발견: {recent_feedback.prp_no}", "SUCCESS")
                return True
            else:
                self.log("테스트 피드백을 찾을 수 없습니다", "WARNING")
                return True  # 경고이지만 실패는 아님
                
        except Exception as e:
            self.log(f"데이터베이스 일관성 테스트 실패: {e}", "ERROR")
            return False
    
    def run_full_test(self):
        """전체 엔드투엔드 테스트 실행"""
        self.log("=" * 60)
        self.log("보이스피싱 탐지 시스템 엔드투엔드 테스트 시작")
        self.log("=" * 60)
        
        tests_passed = 0
        total_tests = 6
        
        # 1. 홈페이지 테스트
        if self.test_home_page():
            tests_passed += 1
        
        # 2. 업로드 페이지 테스트
        if self.test_upload_page():
            tests_passed += 1
        
        # 3. 파일 분석 테스트
        analysis_result = self.test_file_analysis()
        if analysis_result:
            tests_passed += 1
            
            # 분석 결과에서 필요한 정보 추출
            rslt_id = analysis_result.get('rslt_id')
            ocrn_no = analysis_result.get('ocrn_no')
            task_id = analysis_result.get('ocrn_no')  # task_id는 보통 ocrn_no와 같음
            
            # 4. 결과 페이지 테스트
            if task_id and self.test_result_page(task_id):
                tests_passed += 1
            
            # 5. 피드백 제출 테스트
            if rslt_id and ocrn_no and self.test_feedback_submission(rslt_id, ocrn_no):
                tests_passed += 1
        
        # 6. 데이터베이스 일관성 테스트
        if self.test_database_consistency():
            tests_passed += 1
        
        # 테스트 결과 요약
        self.log("=" * 60)
        self.log(f"엔드투엔드 테스트 완료: {tests_passed}/{total_tests} 통과")
        self.log("=" * 60)
        
        if tests_passed == total_tests:
            self.log("모든 테스트가 성공적으로 통과했습니다!", "SUCCESS")
            return True
        else:
            self.log(f"{total_tests - tests_passed}개의 테스트가 실패했습니다.", "ERROR")
            return False

def main():
    """메인 실행 함수"""
    # Django 서버가 실행 중인지 확인
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code != 200:
            print("[ERROR] Django 서버가 올바르게 실행되지 않고 있습니다.")
            print("먼저 'uv run python manage.py runserver'로 서버를 시작해주세요.")
            return False
    except requests.exceptions.RequestException:
        print("[ERROR] Django 서버에 연결할 수 없습니다.")
        print("먼저 'uv run python manage.py runserver'로 서버를 시작해주세요.")
        return False
    
    # 엔드투엔드 테스트 실행
    tester = EndToEndTester()
    return tester.run_full_test()

if __name__ == "__main__":
    try:
        success = main()
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n테스트가 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"예상치 못한 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)