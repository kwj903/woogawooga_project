
import os
import json
import pandas as pd

# 기본 경로 설정
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 입력 폴더: 'datas'
input_dir = os.path.join(base_dir, 'datas')

# 출력 폴더: 'dataset'
output_dir = os.path.join(base_dir, 'dataset')
output_csv_path = os.path.join(output_dir, "normal_dataset3.csv")
mapping_csv_path = os.path.join(output_dir, "file_name_mapping.csv")

# 출력 폴더가 없으면 생성
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 모든 JSON 파일 경로 가져오기
json_files = []
if os.path.exists(input_dir):
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))
else:
    print(f"Error: Input directory '{input_dir}' not found.")

# 데이터를 저장할 리스트 및 파일 매핑 정보 초기화
all_data = []
file_mapping = []
file_counter = 1

# 각 JSON 파일을 순회하며 데이터 추출
for file_path in json_files:
    original_file_name = os.path.basename(file_path)
    simple_file_name = f"file_{file_counter}"
    file_mapping.append({
        "original_name": original_file_name,
        "simple_name": simple_file_name
    })
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

            # 메타데이터 추출
            category = json_data.get("Noise", {}).get("Speaker1NoiseCategory")
            if not category:
                 category = json_data.get("info", {}).get("category")

            # 화자(SpeakerNo)를 숫자로 매핑하기 위한 딕셔너리와 카운터
            speaker_map = {}
            next_speaker_id = 1
            
            # 두 가지 다른 JSON 구조 처리
            if "Conversation" in json_data: # 자유대화 형식
                conversation = json_data.get("Conversation", [])
                for utterance in conversation:
                    speaker_no = utterance.get("SpeakerNo")
                    text = utterance.get("Text")
                    emotion_target = utterance.get("SpeakerEmotionTarget")

                    if speaker_no and text:
                        if speaker_no not in speaker_map:
                            speaker_map[speaker_no] = next_speaker_id
                            next_speaker_id += 1
                        spk = speaker_map[speaker_no]

                        all_data.append({
                            "file_name": simple_file_name,
                            "category": category,
                            "subcategory": emotion_target,
                            "spk": spk,
                            "msg": text
                        })
            elif "utterances" in json_data: # 공감형 대화 형식
                info = json_data.get("info", {})
                subcategory = info.get("relation")
                utterances = json_data.get("utterances", [])
                for utterance in utterances:
                    role = utterance.get("role")
                    message = utterance.get("text")

                    if role and message:
                        if role not in speaker_map:
                            speaker_map[role] = next_speaker_id
                            next_speaker_id += 1
                        spk = speaker_map[role]

                        all_data.append({
                            "file_name": simple_file_name,
                            "category": info.get("speaker_emotion"),
                            "subcategory": subcategory,
                            "spk": spk,
                            "msg": message
                        })
        file_counter += 1

    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from {file_path}")
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")

# 데이터가 있을 경우에만 처리
if all_data:
    # DataFrame 생성
    df = pd.DataFrame(all_data, columns=['file_name', 'category', 'subcategory', 'spk', 'msg'])
    mapping_df = pd.DataFrame(file_mapping)
    
    # CSV 파일로 저장
    df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    mapping_df.to_csv(mapping_csv_path, index=False, encoding='utf-8-sig')
    
    print(f"Successfully created {output_csv_path} with {len(df)} rows.")
    print(f"Successfully created mapping file: {mapping_csv_path}")
else:
    print("No data was extracted. The CSV file was not created.")
