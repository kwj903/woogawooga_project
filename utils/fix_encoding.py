#!/usr/bin/env python
"""
utils 폴더 내 모든 파일의 이모지 및 특수문자를 제거하는 스크립트
"""
import os
import glob
import re

def fix_encoding_issues():
    """이모지 및 특수문자 제거"""
    
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    python_files = glob.glob(os.path.join(utils_dir, "*.py"))
    
    # 이모지 제거 패턴
    emoji_patterns = [
        r'🔍', r'📋', r'🔄', r'✅', r'⚠️', r'❌', r'🔗', r'📏',
        r'🎯', r'📊', r'🆔', r'📤', r'📝', r'💬', r'🎉', r'💡'
    ]
    
    replacements = {
        '🔍': '[검색]',
        '📋': '[정보]', 
        '🔄': '[처리]',
        '✅': '[OK]',
        '⚠️': '[WARNING]',
        '❌': '[ERROR]',
        '🔗': '[연결]',
        '📏': '[측정]',
        '🎯': '[대상]',
        '📊': '[결과]',
        '🆔': '[ID]',
        '📤': '[전송]',
        '📝': '[요약]',
        '💬': '[메시지]',
        '🎉': '[완료]',
        '💡': '[정보]'
    }
    
    updated_files = []
    
    for file_path in python_files:
        if os.path.basename(file_path) == "fix_encoding.py":
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 이모지 교체
            for emoji, replacement in replacements.items():
                if emoji in content:
                    content = content.replace(emoji, replacement)
            
            # Unicode 이스케이프 시퀀스 교체
            unicode_pattern = r'\\U[0-9a-fA-F]{8}'
            content = re.sub(unicode_pattern, '[UNICODE]', content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                updated_files.append(os.path.basename(file_path))
                print(f"[OK] {os.path.basename(file_path)}: 인코딩 수정")
            else:
                print(f"[SKIP] {os.path.basename(file_path)}: 수정 불필요")
                
        except Exception as e:
            print(f"[ERROR] {os.path.basename(file_path)}: 오류 - {e}")
    
    print(f"\n인코딩 수정 완료: {len(updated_files)}개 파일")
    for file_name in updated_files:
        print(f"  - {file_name}")

if __name__ == "__main__":
    fix_encoding_issues()