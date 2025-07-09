
import os
import json
import pandas as pd

# 기본 경로 설정
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
datas_dir = os.path.join(base_dir, 'datas', 'merged')
dataset_dir = os.path.join(base_dir, 'dataset')
output_csv_path = os.path.join(dataset_dir, "normal_dataset.csv")

# 데이터셋 폴더가 없으면 생성
if not os.path.exists(dataset_dir):
    os.makedirs(dataset_dir)

# 모든 JSON 파일 경로 가져오기
json_files = []
for root, _, files in os.walk(datas_dir):
    for file in files:
        if file.endswith(".json"):
            json_files.append(os.path.join(root, file))

# 데이터를 저장할 리스트 초기화
all_data = []

# 각 JSON 파일을 순회하며 데이터 추출
for file_path in json_files:
    file_name = os.path.basename(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            
            info = json_data.get("info", {})
            category = info.get("speaker_emotion")
            subcategory = info.get("relation")
            
            dialogs = json_data.get("utterances", [])
            
            # 화자(role)를 숫자로 매핑하기 위한 딕셔너리와 카운터
            speaker_map = {}
            next_speaker_id = 1

            for dialog in dialogs:
                role = dialog.get("role")
                message = dialog.get("text")

                if role and message:
                    # 새로운 화자일 경우, 맵에 추가
                    if role not in speaker_map:
                        speaker_map[role] = next_speaker_id
                        next_speaker_id += 1
                    
                    spk = speaker_map[role]

                    all_data.append({
                        "file_name": file_name,
                        "category": category,
                        "subcategory": subcategory,
                        "spk": spk,
                        "msg": message
                    })
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from {file_path}")
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")

# 새로운 데이터가 있을 경우에만 처리
if all_data:
    # DataFrame 생성
    df = pd.DataFrame(all_data, columns=['file_name', 'category', 'subcategory', 'spk', 'msg'])
    
    # CSV 파일로 저장
    df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f"Successfully created {output_csv_path} with {len(df)} rows.")
else:
    print("No data was extracted. The CSV file was not created.")
