import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path
import platform
from matplotlib import font_manager, rc

plt.rcParams["axes.unicode_minus"] = False
if platform.system() == "Windows":
    font_path = "C:/Windows/Fonts/malgun.ttf"
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    rc("font", family=font_name)
else:
    rc("font", family="AppleGothic")

sns.set(style="whitegrid")

plt.rcParams["axes.unicode_minus"] = False
if platform.system() == "Windows":
    font_path = "C:/Windows/Fonts/malgun.ttf"
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    rc("font", family=font_name)
def analyze_phishing_text_length():
    """
    phishing_6000_final.csv 파일을 읽어, file_id별로 text를 합친 후
    글자 수 분포 통계와 그래프를 생성합니다.
    """
    # --- 설정 ---
    # 이 스크립트 파일의 위치를 기준으로 상대 경로를 설정합니다.
    # 스크립트가 'dataset_create/Woojae'에 있으므로, 상위 폴더로 두 번 이동하여 루트에 접근합니다.
    try:
        script_dir = os.path.dirname(__file__)
    except NameError:
        # 대화형 환경(예: Jupyter)에서 실행될 경우를 대비
        script_dir = os.getcwd()

    base_dir = os.path.join(script_dir, "..", "..")
    input_file = os.path.join(base_dir, "dataset", "phishing_6000_final.csv")
    output_dir = os.path.join(base_dir, "datas/analysisData")

    # 분석 결과 저장 폴더 생성
    os.makedirs(output_dir, exist_ok=True)

    # 한글 폰트 설정 (Windows: Malgun Gothic, Mac: AppleGothic)
    try:
        if os.name == 'nt': # Windows
            plt.rcParams['font.family'] = 'Malgun Gothic'
        elif os.name == 'posix': # Mac/Linux
            plt.rcParams['font.family'] = 'AppleGothic'
    except Exception as e:
        print(f"폰트 설정 중 오류 발생: {e}. 그래프의 한글이 깨질 수 있습니다.")
    plt.rcParams['axes.unicode_minus'] = False

    # --- 데이터 불러오기 ---
    print(f"'{os.path.abspath(input_file)}' 에서 데이터를 불러옵니다...")
    try:
        df = pd.read_csv(input_file)
        print("데이터 불러오기 완료.")
    except FileNotFoundError:
        print(f"오류: 파일을 찾을 수 없습니다. '{os.path.abspath(input_file)}' 경로를 확인하세요.")
        return

    # --- 데이터 분석 ---
    print("file_id를 기준으로 텍스트를 병합하고 글자 수를 계산합니다...")
    # NaN 값을 빈 문자열로 처리하여 오류 방지
    df['text'] = df['text'].fillna('')
    # 그룹화 및 텍스트 병합
    grouped_df = df.groupby('file_id')['text'].apply(lambda x: ' '.join(x)).reset_index()

    # 합쳐진 text의 글자 수 계산
    grouped_df['char_count'] = grouped_df['text'].str.len()
    print("계산 완료.")

    # --- 통계 출력 ---
    print("\n--- file_id 당 글자 수 통계 ---")
    stats = grouped_df['char_count'].describe()
    print(stats)
    # 통계 결과를 텍스트 파일로 저장
    stats_path = os.path.join(output_dir, "phishing_char_count_stats.txt")
    with open(stats_path, 'w', encoding='utf-8') as f:
        f.write("file_id당 글자 수 통계\n")
        f.write(str(stats))
    print(f"통계 정보가 '{stats_path}'에 저장되었습니다.")
    print("---------------------------------")

    # --- 시각화 ---
    print("\n글자 수 분포 그래프를 생성합니다...")
    plt.figure(figsize=(12, 6))
    sns.histplot(data=grouped_df, x='char_count', kde=True, bins=50)
    plt.title('file_id당 전체 Text 글자 수 분포')
    plt.xlabel('글자 수')
    plt.ylabel('파일 ID 개수')
    plt.grid(True)

    # 그래프를 이미지 파일로 저장
    output_image_path = os.path.join(output_dir, "phishing_char_count_distribution.png")
    plt.savefig(output_image_path)
    print(f"그래프가 '{output_image_path}'에 저장되었습니다.")

    # 화면에 그래프 표시 (스크립트 실행 시 주석 처리 가능)
    # plt.show()

    print("\n분석이 완료되었습니다.")

if __name__ == '__main__':
    analyze_phishing_text_length()
