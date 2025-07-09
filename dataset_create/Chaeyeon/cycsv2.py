# %%
import pandas as pd

# 원본 파일 불러오기
df = pd.read_csv("C:/Users/user/Downloads/0708/woogawooga_project/dataset_create/LLM_phishing_data.csv")


# %%
# 숫자 추출 - 새 컬럼
df["file_num"] = df["file_name"].str.extract(r"phishing_(\d+)").astype(int)

# 숫자 기준 안정 정렬 (같은 file_name 내 순서 유지)
df = df.sort_values(by="file_num", kind="stable").drop(columns="file_num").reset_index(drop=True)

# 확인
print(df.head())

# %%
df.tail()

# %%
#결과저장
df.to_csv("LLM_phishing_data_sorted.csv", index=False, encoding="utf-8-sig")

# %%
#유튜브 보이스피싱 데이터 
import pandas as pd

# 데이터 불러오기
df = pd.read_csv("C:/Users/user/Downloads/0708/woogawooga_project/dataset_create/merged_youtube_data.csv")  # ← 여기에 파일 경로 입력

# file_name별로 고유한 값 추출
unique_names = df["file_name"].unique()

# 새로운 file_name 매핑 딕셔너리 생성
name_mapping = {
    old_name: f"phishing_{1301 + i:04d}" for i, old_name in enumerate(unique_names)
}

# file_name 치환
df["file_name"] = df["file_name"].map(name_mapping)


# %%
df.head()

# %%
# 저장
df.to_csv("phishing_llmyoutube.csv", index=False, encoding="utf-8-sig")

# %% [markdown]
# # LLM과 유튜브 csv 병합

# %%
import pandas as pd
df1 = pd.read_csv("C:/Users/user/Downloads/0708/woogawooga_project/dataset_create/LLM_phishing_data_sorted.csv") #LLM 1~1300순서 csv
df2 = pd.read_csv("C:/Users/user/Downloads/0708/woogawooga_project/dataset_create/phishing_llmyoutube.csv") #유튜브 1301~1367 csv

# 데이터프레임 결합
df_combined = pd.concat([df1, df2], ignore_index=True)

# 결과 확인
print(df_combined.head())

# %%
print(df_combined.tail())

# %%
# 저장
df_combined.to_csv("csv_merged1.csv", index=False)


