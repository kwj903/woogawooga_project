# %%
import pandas as pd

# 원본 파일 불러오기
df = pd.read_csv("C:/Users/user/Downloads/0708/woogawooga_project/dataset_create/phishing_data.csv")

# 문장 분리 + speaker 자동번갈기
all_rows = []

for _, row in df.iterrows():
    file_id = row["file_name"]
    phishing_type = row["phishing_type"]
    text = row["text"]

    if pd.isna(text):
        continue

    # 문장 분리
    sentences = [s.strip() for s in str(text).split("\n") if s.strip()]
    
    # speaker 0, 1 번갈아가며 부여
    for i, sentence in enumerate(sentences):
        speaker = i % 2  # 0, 1, 0, 1, ...
        all_rows.append({
            "file_name": file_id,
            "phishing_type": phishing_type,
            "speaker": speaker,
            "text": sentence
        })

# 새 데이터프레임 생성
df_result = pd.DataFrame(all_rows)

#저장
df_result.to_csv("phishing_split_speaker.csv", index=False, encoding="utf-8-sig")


# %%


# %%


# %%



