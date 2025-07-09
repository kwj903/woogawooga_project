'''
이 스크립트는 'datas' 폴더 하위의 모든 JSON 파일에서 대화 내용을 추출하여 
하나의 CSV 파일로 만들거나 기존 파일에 추가하는 작업을 수행합니다.

주요 기능:
- 'datas' 폴더 내의 모든 JSON 파일을 재귀적으로 탐색합니다.
- 각 JSON 파일에서 파일 이름, 카테고리, 하위 카테고리, 화자(speaker), 메시지(text)를 추출합니다.
- 추출된 데이터를 pandas DataFrame으로 변환합니다.
- 'dataset/normal_dataset.csv' 파일이 이미 존재하면 기존 데이터를 불러와 새로운 데이터와 병합합니다.
- 중복된 데이터는 제거하고, file_name을 기준으로 오름차순 정렬한 후 최종적으로 'dataset' 폴더에 'normal_dataset.csv'라는 이름으로 저장합니다.
'''

import os
import json
import pandas as pd

# 기본 경로 설정
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
datas_dir = os.path.join(base_dir, 'datas')
dataset_dir = os.path.join(base_dir, 'dataset')
output_csv_path = os.path.join(dataset_dir, "normal_dataset.csv")

# 데이터셋 폴더가 없으면 생성
if not os.path.exists(dataset_dir):
    os.makedirs(dataset_dir)

# 컬럼 정의
columns = ['file_name', 'category', 'subcategory', 'spk', 'msg']

# 기존 CSV 파일이 있으면 데이터 불러오기
if os.path.exists(output_csv_path):
    try:
        existing_df = pd.read_csv(output_csv_path)
    except pd.errors.EmptyDataError:
        existing_df = pd.DataFrame(columns=columns)
else:
    existing_df = pd.DataFrame(columns=columns)

# 모든 JSON 파일 경로 가져오기
json_files = []
for root, _, files in os.walk(datas_dir):
    for file in files:
        if file.endswith(".json"):
            json_files.append(os.path.join(root, file))

# 데이터를 저장할 리스트 초기화
new_data = []

# 각 JSON 파일을 순회하며 데이터 추출
for file_path in json_files:
    file_name = os.path.basename(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            type_info = json_data.get("dataSet", {}).get("typeInfo", {})
            category = type_info.get("category")
            subcategory = type_info.get("subcategory")
            dialogs = json_data.get("dataSet", {}).get("dialogs", [])
            
            for dialog in dialogs:
                speaker = dialog.get("speaker")
                message = dialog.get("text")
                if speaker and message:
                    new_data.append({
                        "file_name": file_name,
                        "category": category,
                        "subcategory": subcategory,
                        "spk": speaker,
                        "msg": message
                    })
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from {file_path}")
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")

# 새로운 데이터가 있을 경우에만 처리
if new_data:
    new_df = pd.DataFrame(new_data, columns=columns)
    
    # 기존 데이터와 새로운 데이터 병합
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    
    # 중복 데이터 제거
    combined_df.drop_duplicates(subset=columns, keep='last', inplace=True)
    
    # file_name을 기준으로 오름차순 정렬
    combined_df.sort_values(by='file_name', inplace=True)
    
    # CSV 파일로 저장
    combined_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f"Successfully updated and sorted {output_csv_path}")
else:
    # 새로운 데이터가 없더라도 기존 데이터를 정렬하여 다시 저장
    if not existing_df.empty:
        existing_df.sort_values(by='file_name', inplace=True)
        existing_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
        print(f"No new data. Existing data in {output_csv_path} has been sorted.")
    else:
        print("No new data was extracted and existing data is empty. The CSV file was not updated.")
