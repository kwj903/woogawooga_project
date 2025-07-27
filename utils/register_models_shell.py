"""
Django shell에서 실행할 ModelRegistry 등록 코드
"""

from woogawooga.models import ModelRegistry
from pathlib import Path
import os

def register_all_models():
    """models 폴더의 모든 모델을 ModelRegistry에 등록"""
    
    # models 폴더 경로
    base_dir = Path(__file__).resolve().parent.parent
    models_dir = base_dir / 'models'
    
    # 등록할 모델 정보 (파일명 -> 모델 정보)
    model_info = {
        # 1차 머신러닝 모델들 (pickle 기반)
        'stacking_v1.pkl': {
            'mdl_id': 'STACK_V1',
            'mdl_nm': 'Stacking 앙상블 모델 v1 (1차)',
            'use_yn': 'N'  # 구버전이므로 비활성화
        },
        'stacking_v2.pkl': {
            'mdl_id': 'STACK_V2',
            'mdl_nm': 'Stacking 앙상블 모델 v2 (1차 주력)',
            'use_yn': 'Y'  # 현재 1차 모델로 사용
        },
        'Bagging_v1.pkl': {
            'mdl_id': 'BAG_V1',
            'mdl_nm': 'Bagging 앙상블 모델 v1',
            'use_yn': 'N'
        },
        'Bagging_v2.pkl': {
            'mdl_id': 'BAG_V2',
            'mdl_nm': 'Bagging 앙상블 모델 v2',
            'use_yn': 'N'
        },
        'logistic_v1.pkl': {
            'mdl_id': 'LR_V1',
            'mdl_nm': 'Logistic Regression v1',
            'use_yn': 'N'
        },
        'logistic_v2.pkl': {
            'mdl_id': 'LR_V2',
            'mdl_nm': 'Logistic Regression v2',
            'use_yn': 'N'
        },
        'logistic2_v1.pkl': {
            'mdl_id': 'LR2_V1',
            'mdl_nm': 'Logistic Regression 2단계 v1',
            'use_yn': 'N'
        },
        'logistic3_v2.pkl': {
            'mdl_id': 'LR3_V2',
            'mdl_nm': 'Logistic Regression 3단계 v2',
            'use_yn': 'N'
        },
        'lgbm_model_v2.pkl': {
            'mdl_id': 'LGBM_V2',
            'mdl_nm': 'LightGBM 모델 v2 (2차 백업)',
            'use_yn': 'N'  # 백업용으로만 사용
        },
        
        # 2차 딥러닝 모델 (PyTorch 기반)
        'kobert_2nd_model_runpod.pth': {
            'mdl_id': 'KOBERT_2ND',
            'mdl_nm': 'KoBERT+LSTM+Attention 모델 (2차 주력)',
            'use_yn': 'Y'  # 현재 2차 모델로 사용
        }
    }
    
    print("=" * 60)
    print("ModelRegistry 모델 등록 시작")
    print("=" * 60)
    
    registered_count = 0
    updated_count = 0
    
    for file_name, info in model_info.items():
        file_path = models_dir / file_name
        
        # 파일 존재 확인
        if not file_path.exists():
            print(f"❌ 파일 없음: {file_name}")
            continue
        
        # 파일 크기 확인
        file_size = file_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        try:
            # 기존 레코드 확인
            model_registry, created = ModelRegistry.objects.get_or_create(
                mdl_id=info['mdl_id'],
                defaults={
                    'mdl_nm': info['mdl_nm'],
                    'use_yn': info['use_yn']
                }
            )
            
            if created:
                print(f"✅ 새로 등록: {info['mdl_id']} - {info['mdl_nm']}")
                print(f"   파일: {file_name} ({file_size_mb:.1f}MB)")
                print(f"   사용여부: {info['use_yn']}")
                registered_count += 1
            else:
                # 기존 레코드 업데이트
                model_registry.mdl_nm = info['mdl_nm']
                model_registry.use_yn = info['use_yn']
                model_registry.save()
                
                print(f"🔄 업데이트: {info['mdl_id']} - {info['mdl_nm']}")
                print(f"   파일: {file_name} ({file_size_mb:.1f}MB)")
                print(f"   사용여부: {info['use_yn']}")
                updated_count += 1
                
        except Exception as e:
            print(f"❌ 등록 실패: {info['mdl_id']} - {e}")
        
        print()
    
    print("=" * 60)
    print("등록 완료 요약")
    print("=" * 60)
    print(f"새로 등록된 모델: {registered_count}개")
    print(f"업데이트된 모델: {updated_count}개")
    print(f"총 처리된 모델: {registered_count + updated_count}개")
    print()
    
    # 현재 등록된 모든 모델 출력
    print("현재 등록된 모든 모델:")
    print("-" * 60)
    all_models = ModelRegistry.objects.all().order_by('mdl_id')
    
    for model in all_models:
        status = "🟢 활성" if model.use_yn == 'Y' else "🔴 비활성"
        print(f"{model.mdl_id:12} | {status} | {model.mdl_nm}")
    
    print(f"\n총 {all_models.count()}개 모델이 등록되어 있습니다.")

# 실행
register_all_models()