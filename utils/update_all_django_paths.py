#!/usr/bin/env python
"""
utils 폴더 내 모든 Django 파일의 경로 설정을 일괄 수정하는 스크립트
"""
import os
import glob

def update_django_paths():
    """Django 경로 설정 일괄 수정"""
    
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    python_files = glob.glob(os.path.join(utils_dir, "*.py"))
    
    # 기존 import 패턴과 새로운 import 패턴
    old_pattern = """import os
import django

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()"""

    new_pattern = """import os
import sys
import django

# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()"""

    # 다른 패턴들도 처리
    old_pattern_2 = """# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()"""

    new_pattern_2 = """# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()"""

    updated_files = []
    
    for file_path in python_files:
        if os.path.basename(file_path) == "update_all_django_paths.py":
            continue  # 이 스크립트 자체는 제외
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 패턴 교체
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                print(f"[OK] {os.path.basename(file_path)}: 전체 패턴 교체")
            elif old_pattern_2 in content and 'sys.path.insert' not in content:
                # sys import 추가
                if 'import sys' not in content:
                    content = content.replace('import os', 'import os\nimport sys')
                # 패턴 교체
                content = content.replace(old_pattern_2, new_pattern_2)
                print(f"[OK] {os.path.basename(file_path)}: 부분 패턴 교체")
            else:
                print(f"[SKIP] {os.path.basename(file_path)}: 수정 불필요")
                continue
            
            # 변경사항이 있으면 파일 저장
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                updated_files.append(os.path.basename(file_path))
                
        except Exception as e:
            print(f"[ERROR] {os.path.basename(file_path)}: 오류 - {e}")
    
    print(f"\n업데이트 완료: {len(updated_files)}개 파일")
    for file_name in updated_files:
        print(f"  - {file_name}")

if __name__ == "__main__":
    update_django_paths()