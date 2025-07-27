-- ModelRegistry에 models 폴더의 모든 모델 등록하는 SQL
-- MySQL/MariaDB용

-- 기존 데이터가 있으면 업데이트, 없으면 삽입 (UPSERT)

-- 1차 머신러닝 모델들 (pickle 기반)
INSERT INTO ModelRegistry (mdl_id, mdl_nm, use_yn) VALUES 
('STACK_V1', 'Stacking 앙상블 모델 v1 (1차)', 'N')
ON DUPLICATE KEY UPDATE 
mdl_nm = VALUES(mdl_nm), use_yn = VALUES(use_yn);

INSERT INTO ModelRegistry (mdl_id, mdl_nm, use_yn) VALUES 
('STACK_V2', 'Stacking 앙상블 모델 v2 (1차 주력)', 'Y')
ON DUPLICATE KEY UPDATE 
mdl_nm = VALUES(mdl_nm), use_yn = VALUES(use_yn);

INSERT INTO ModelRegistry (mdl_id, mdl_nm, use_yn) VALUES 
('BAG_V1', 'Bagging 앙상블 모델 v1', 'N')
ON DUPLICATE KEY UPDATE 
mdl_nm = VALUES(mdl_nm), use_yn = VALUES(use_yn);

INSERT INTO ModelRegistry (mdl_id, mdl_nm, use_yn) VALUES 
('BAG_V2', 'Bagging 앙상블 모델 v2', 'N')
ON DUPLICATE KEY UPDATE 
mdl_nm = VALUES(mdl_nm), use_yn = VALUES(use_yn);

INSERT INTO ModelRegistry (mdl_id, mdl_nm, use_yn) VALUES 
('LR_V1', 'Logistic Regression v1', 'N')
ON DUPLICATE KEY UPDATE 
mdl_nm = VALUES(mdl_nm), use_yn = VALUES(use_yn);

INSERT INTO ModelRegistry (mdl_id, mdl_nm, use_yn) VALUES 
('LR_V2', 'Logistic Regression v2', 'N')
ON DUPLICATE KEY UPDATE 
mdl_nm = VALUES(mdl_nm), use_yn = VALUES(use_yn);

INSERT INTO ModelRegistry (mdl_id, mdl_nm, use_yn) VALUES 
('LR2_V1', 'Logistic Regression 2단계 v1', 'N')
ON DUPLICATE KEY UPDATE 
mdl_nm = VALUES(mdl_nm), use_yn = VALUES(use_yn);

INSERT INTO ModelRegistry (mdl_id, mdl_nm, use_yn) VALUES 
('LR3_V2', 'Logistic Regression 3단계 v2', 'N')
ON DUPLICATE KEY UPDATE 
mdl_nm = VALUES(mdl_nm), use_yn = VALUES(use_yn);

INSERT INTO ModelRegistry (mdl_id, mdl_nm, use_yn) VALUES 
('LGBM_V2', 'LightGBM 모델 v2 (2차 백업)', 'N')
ON DUPLICATE KEY UPDATE 
mdl_nm = VALUES(mdl_nm), use_yn = VALUES(use_yn);

-- 2차 딥러닝 모델 (PyTorch 기반)
INSERT INTO ModelRegistry (mdl_id, mdl_nm, use_yn) VALUES 
('KOBERT_2ND', 'KoBERT+LSTM+Attention 모델 (2차 주력)', 'Y')
ON DUPLICATE KEY UPDATE 
mdl_nm = VALUES(mdl_nm), use_yn = VALUES(use_yn);

-- 등록된 모델 확인
SELECT mdl_id, mdl_nm, use_yn, 
       CASE use_yn WHEN 'Y' THEN '🟢 활성' ELSE '🔴 비활성' END as 상태
FROM ModelRegistry 
ORDER BY mdl_id;