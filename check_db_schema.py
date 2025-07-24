#!/usr/bin/env python
"""
데이터베이스 스키마 확인 스크립트
Django shell에서 실행: python manage.py shell < check_db_schema.py
"""

import os
import django
from django.conf import settings
from django.db import connection

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def check_database_schema():
    """데이터베이스 스키마 확인"""
    cursor = connection.cursor()
    
    print("=" * 60)
    print("🔍 데이터베이스 스키마 확인")
    print("=" * 60)
    
    # InferenceResult 테이블 구조 확인
    try:
        cursor.execute("DESCRIBE InferenceResult")
        columns = cursor.fetchall()
        
        print("\n📋 InferenceResult 테이블 구조:")
        print("-" * 50)
        print(f"{'필드명':<20} {'타입':<15} {'NULL':<5} {'키':<5} {'기본값':<10}")
        print("-" * 50)
        
        for column in columns:
            field_name = column[0]
            field_type = column[1]
            is_null = column[2]
            key = column[3]
            default = column[4] if column[4] is not None else ''
            
            print(f"{field_name:<20} {field_type:<15} {is_null:<5} {key:<5} {str(default):<10}")
            
            # file_id 필드 특별 확인
            if field_name == 'file_id':
                print(f"🎯 file_id 필드: {field_type}")
                if 'varchar(20)' in field_type.lower():
                    print("⚠️  문제 발견: file_id가 여전히 20자로 제한되어 있습니다!")
                elif 'varchar(50)' in field_type.lower():
                    print("✅ file_id가 50자로 올바르게 설정되었습니다.")
                    
    except Exception as e:
        print(f"❌ 테이블 구조 확인 실패: {str(e)}")
    
    # Migration 적용 상태 확인
    try:
        cursor.execute("SELECT app, name, applied FROM django_migrations WHERE app = 'woogawooga' ORDER BY applied DESC LIMIT 10")
        migrations = cursor.fetchall()
        
        print(f"\n🔄 최근 Migration 기록:")
        print("-" * 50)
        for migration in migrations:
            app, name, applied = migration
            print(f"{name:<40} {applied}")
            
        # 우리가 만든 migration 확인
        cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app = 'woogawooga' AND name = '0003_alter_inferenceresult_file_id'")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print("✅ 0003_alter_inferenceresult_file_id migration이 적용되었습니다.")
        else:
            print("⚠️  0003_alter_inferenceresult_file_id migration이 적용되지 않았습니다!")
            
    except Exception as e:
        print(f"❌ Migration 기록 확인 실패: {str(e)}")
    
    # 현재 데이터베이스 연결 정보
    print(f"\n🔗 데이터베이스 연결 정보:")
    print(f"   엔진: {settings.DATABASES['default']['ENGINE']}")
    print(f"   데이터베이스: {settings.DATABASES['default']['NAME']}")
    print(f"   호스트: {settings.DATABASES['default']['HOST']}")
    print(f"   포트: {settings.DATABASES['default']['PORT']}")
    
    cursor.close()

def test_uuid_length():
    """UUID 길이 테스트"""
    import uuid
    
    print(f"\n📏 UUID 길이 테스트:")
    print("-" * 30)
    
    test_uuid = str(uuid.uuid4())
    print(f"완전한 UUID: '{test_uuid}' (길이: {len(test_uuid)})")
    
    # 하이픈 제거
    uuid_no_dash = test_uuid.replace('-', '')
    print(f"하이픈 제거: '{uuid_no_dash}' (길이: {len(uuid_no_dash)})")
    
    # 20자로 단축
    uuid_short = test_uuid.replace('-', '')[:20]
    print(f"20자 단축: '{uuid_short}' (길이: {len(uuid_short)})")

if __name__ == "__main__":
    check_database_schema()
    test_uuid_length()
    print("\n" + "=" * 60)
    print("스키마 확인 완료!")
    print("=" * 60)