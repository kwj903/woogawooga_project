#!/usr/bin/env python
"""
views.py에 포괄적인 로깅 로직을 추가하는 스크립트
모든 주요 진행 과정을 SystemLog 테이블에 기록하도록 수정
"""
import os
import sys

# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def add_comprehensive_logging():
    """views.py에 포괄적인 로깅 추가"""
    
    views_path = "D:/workspace/woogawooga_project/woogawooga/views.py"
    
    # 추가할 로깅 함수
    logging_helper_code = '''
def log_system_info(level, message, file_name=None, ip_address=None):
    """시스템 로그를 데이터베이스에 기록하는 헬퍼 함수"""
    try:
        SystemLog.objects.create(
            level=level,
            message=message,
            file_name=file_name or 'SYSTEM',
            ip_address=ip_address,
            created_at=timezone.now()
        )
        logger.info(f"[DB_LOG] {level}: {message}")
    except Exception as e:
        logger.error(f"시스템 로그 저장 실패: {e}")
'''
    
    try:
        with open(views_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 로깅 헬퍼 함수가 이미 있는지 확인
        if "def log_system_info" in content:
            print("[INFO] 로깅 헬퍼 함수가 이미 존재합니다.")
        else:
            # generate_short_id 함수 다음에 로깅 헬퍼 함수 추가
            insertion_point = content.find("def get_client_ip(request):")
            if insertion_point == -1:
                print("[ERROR] 삽입 지점을 찾을 수 없습니다.")
                return False
            
            # 로깅 헬퍼 함수 삽입
            content = content[:insertion_point] + logging_helper_code + "\n" + content[insertion_point:]
            print("[OK] 로깅 헬퍼 함수 추가됨")
        
        # 기존 logger.info를 log_system_info로 교체할 주요 지점들
        replacements = [
            # 분석 시작
            ('logger.info(f"=== 분석 요청 시작 ===")', 
             'log_system_info("INFO", "=== 분석 요청 시작 ===", audio_file.name if "audio_file" in locals() else "SYSTEM", client_ip)'),
            
            # VITO STT 시작
            ('logger.info(f"VITO STT 시작: {audio_file.name}")', 
             'log_system_info("INFO", f"VITO STT 시작: {audio_file.name}", audio_file.name, client_ip)'),
            
            # VITO STT 완료
            ('logger.info(f"VITO STT 완료: {len(transcript)} 글자")', 
             'log_system_info("INFO", f"VITO STT 완료: {len(transcript)} 글자", audio_file.name, client_ip)'),
            
            # 1차 모델 분석 시작
            ('logger.info("1차 모델 분석 시작")', 
             'log_system_info("INFO", "1차 모델 분석 시작", audio_file.name, client_ip)'),
            
            # 1차 모델 분석 완료
            ('logger.info(f"1차 모델 분석 완료: {first_model_result}")', 
             'log_system_info("INFO", f"1차 모델 분석 완료: 예측={first_model_result.get(\'prediction\')}, 신뢰도={first_model_result.get(\'confidence\', 0):.3f}", audio_file.name, client_ip)'),
            
            # 2차 모델 분석 시작
            ('logger.info("보류 구간 - 2차 모델 분석 시작")', 
             'log_system_info("INFO", "보류 구간 - 2차 모델 분석 시작", audio_file.name, client_ip)'),
            
            # 2차 모델 분석 완료
            ('logger.info(f"2차 모델 분석 완료: {second_model_result}")', 
             'log_system_info("INFO", f"2차 모델 분석 완료: 예측={second_model_result.get(\'prediction\')}, 신뢰도={second_model_result.get(\'confidence\', 0):.3f}", audio_file.name, client_ip)'),
            
            # LLM 설명 생성 시작
            ('logger.info("LLM 설명 생성 시작")', 
             'log_system_info("INFO", "LLM 설명 생성 시작", audio_file.name, client_ip)'),
            
            # LLM 설명 생성 완료
            ('logger.info(f"LLM 설명 생성 완료: {llm_result}")', 
             'log_system_info("INFO", f"LLM 설명 생성 완료: 유형={llm_result.get(\'phishing_type\', \'Unknown\')}", audio_file.name, client_ip)'),
            
            # 즉시 판별 로그
            ('logger.info(f"1차 모델에서 즉시 판별: {first_model_result[\'decision_type\']}")', 
             'log_system_info("INFO", f"1차 모델에서 즉시 판별: {first_model_result[\'decision_type\']}", audio_file.name, client_ip)'),
        ]
        
        # 교체 적용
        replacement_count = 0
        for old_code, new_code in replacements:
            if old_code in content:
                content = content.replace(old_code, new_code)
                replacement_count += 1
                print(f"[OK] 로깅 교체: {old_code[:50]}...")
        
        print(f"[INFO] 총 {replacement_count}개의 로깅 구문을 교체했습니다.")
        
        # 파일 저장
        with open(views_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("[SUCCESS] views.py 로깅 로직 개선 완료!")
        return True
        
    except Exception as e:
        print(f"[ERROR] 로깅 로직 추가 실패: {e}")
        return False

def add_feedback_logging():
    """피드백 제출 과정에도 상세 로깅 추가"""
    
    views_path = "D:/workspace/woogawooga_project/woogawooga/views.py"
    
    try:
        with open(views_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # submit_feedback 함수에 추가 로깅
        feedback_replacements = [
            # 피드백 요청 시작
            ('logger.info(f"피드백 제출 요청: rslt_id={rslt_id}, ocrn_no={ocrn_no}")', 
             'log_system_info("INFO", f"피드백 제출 요청: rslt_id={rslt_id}, ocrn_no={ocrn_no}", "FEEDBACK_REQUEST", client_ip)'),
            
            # 피드백 완료
            ('logger.info(f"새 피드백 생성: {prp_no}")', 
             'log_system_info("INFO", f"새 피드백 생성: {prp_no} - 사용자 판단: {user_prediction}", inference_result.ocrn_no.trsc_file_nm if inference_result.ocrn_no else "UNKNOWN", client_ip)'),
        ]
        
        for old_code, new_code in feedback_replacements:
            if old_code in content:
                content = content.replace(old_code, new_code)
                print(f"[OK] 피드백 로깅 교체: {old_code[:50]}...")
        
        # 파일 저장
        with open(views_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("[SUCCESS] 피드백 로깅 개선 완료!")
        return True
        
    except Exception as e:
        print(f"[ERROR] 피드백 로깅 추가 실패: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("views.py 포괄적 로깅 로직 추가")
    print("=" * 60)
    
    success1 = add_comprehensive_logging()
    success2 = add_feedback_logging()
    
    if success1 and success2:
        print("\n[SUCCESS] 모든 로깅 로직이 성공적으로 추가되었습니다!")
        print("\n다음 단계:")
        print("1. Django 서버를 재시작하세요.")
        print("2. 음성 파일을 업로드하고 분석을 실행하세요.")
        print("3. 피드백을 제출하세요.")
        print("4. SystemLog 테이블에서 상세한 로그를 확인하세요.")
    else:
        print("\n[ERROR] 로깅 로직 추가 중 일부 실패가 발생했습니다.")