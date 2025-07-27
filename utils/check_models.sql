-- ModelRegistry에 등록된 모든 모델 조회

-- 기본 모델 정보
SELECT 
    mdl_id as '모델ID',
    mdl_nm as '모델명',
    CASE use_yn 
        WHEN 'Y' THEN '🟢 활성' 
        ELSE '🔴 비활성' 
    END as '상태',
    use_yn as '사용여부'
FROM ModelRegistry 
ORDER BY mdl_id;

-- 통계 정보
SELECT '총 등록된 모델 수' as 구분, COUNT(*) as 개수 FROM ModelRegistry
UNION ALL
SELECT '활성 모델 수' as 구분, COUNT(*) as 개수 FROM ModelRegistry WHERE use_yn = 'Y'
UNION ALL
SELECT '비활성 모델 수' as 구분, COUNT(*) as 개수 FROM ModelRegistry WHERE use_yn = 'N';

-- 모델 유형별 분류
SELECT 
    CASE 
        WHEN mdl_id LIKE 'STACK%' THEN 'Stacking'
        WHEN mdl_id LIKE 'BAG%' THEN 'Bagging'
        WHEN mdl_id LIKE 'LR%' THEN 'Logistic Regression'
        WHEN mdl_id LIKE 'LGBM%' THEN 'LightGBM'
        WHEN mdl_id LIKE 'KOBERT%' THEN 'KoBERT (PyTorch)'
        ELSE 'Others'
    END as '모델유형',
    COUNT(*) as '개수',
    GROUP_CONCAT(mdl_id ORDER BY mdl_id) as '모델목록'
FROM ModelRegistry 
GROUP BY 
    CASE 
        WHEN mdl_id LIKE 'STACK%' THEN 'Stacking'
        WHEN mdl_id LIKE 'BAG%' THEN 'Bagging'
        WHEN mdl_id LIKE 'LR%' THEN 'Logistic Regression'
        WHEN mdl_id LIKE 'LGBM%' THEN 'LightGBM'
        WHEN mdl_id LIKE 'KOBERT%' THEN 'KoBERT (PyTorch)'
        ELSE 'Others'
    END
ORDER BY '모델유형';