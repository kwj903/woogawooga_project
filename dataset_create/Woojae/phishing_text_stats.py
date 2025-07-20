import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from wordcloud import WordCloud

# 파일 경로 (원하는 경로로 수정 가능)
# file_path = "../../dataset/phishing_6000_final.csv"
file_path = r"D:\workspace\woogawooga_project\dataset\phishing_6000_final.csv"
output_dir = r"D:\workspace\woogawooga_project\datas"

if not os.path.exists(file_path):
    raise FileNotFoundError(f"❌ 파일이 존재하지 않습니다: {file_path}")
os.makedirs(output_dir, exist_ok=True)

# 데이터 불러오기
df = pd.read_csv(file_path)

# file_name 기준 텍스트 합치기
grouped = (
    df.groupby("file_id")["text"].apply(lambda x: " ".join(map(str, x))).reset_index()
)
grouped["char_count"] = grouped["text"].apply(len)

# 통계 요약 저장
stats_summary = grouped["char_count"].describe()
with open(
    os.path.join(output_dir, "char_count_summary.txt"), "w", encoding="utf-8"
) as f:
    f.write("글자 수 통계 요약:\n")
    f.write(str(stats_summary))

# 히스토그램
plt.figure(figsize=(10, 6))
sns.histplot(grouped["char_count"], bins=30, kde=True)
plt.title("글자 수 분포 (file_name 기준)")
plt.xlabel("글자 수")
plt.ylabel("파일 개수")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "char_count_histogram.png"))
plt.close()

# 박스플롯
plt.figure(figsize=(8, 4))
sns.boxplot(x=grouped["char_count"])
plt.title("글자 수 박스플롯")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "char_count_boxplot.png"))
plt.close()

# 워드클라우드 생성
all_text = " ".join(grouped["text"])
wordcloud = WordCloud(
    font_path="malgun.ttf", width=800, height=400, background_color="white"
).generate(all_text)
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "wordcloud.png"))
plt.close()

print("✅ 분석 완료! 결과 파일:")
print(f"- 통계 요약: {output_dir}\\char_count_summary.txt")
print(f"- 히스토그램: {output_dir}\\char_count_histogram.png")
print(f"- 박스플롯: {output_dir}\\char_count_boxplot.png")
print(f"- 워드클라우드: {output_dir}\\wordcloud.png")
