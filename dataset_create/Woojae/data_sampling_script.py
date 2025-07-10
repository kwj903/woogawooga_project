import pandas as pd

try:
    file_path = 'dataset/normal_dataset3.csv'
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"'{file_path}' 파일을 성공적으로 불러왔습니다. (총 {len(df)}개 행)")
    print("-" * 50)

    msg_lengths = df.groupby('file_name')['msg'].apply(lambda x: len(''.join(str(s) for s in x)))
    print("-" * 50)

    count_under_1000 = msg_lengths[msg_lengths <= 1000].shape[0]
    print(f"▶ 메시지 총 길이가 1000자 이하인 데이터(file_name 기준)의 개수:  {count_under_1000}개")
    print("--------------------------------------------------")

    print("글자 길이 기준으로 데이터셋을 샘플링합니다...")
    short_files = msg_lengths[msg_lengths <= 500].index
    medium_files = msg_lengths[(msg_lengths > 500) & (msg_lengths <= 1000)].index
    long_files = msg_lengths[msg_lengths > 1000].index

    short_sample = short_files.to_series().sample(frac=0.70, random_state=42)
    medium_sample = medium_files.to_series().sample(frac=0.25, random_state=42)
    long_sample = long_files.to_series().sample(frac=0.05, random_state=42)

    final_filenames = pd.concat([short_sample, medium_sample, long_sample]).index

    final_df = df[df['file_name'].isin(final_filenames)].reset_index(drop=True)

    print("\n▶ 최종 샘플링된 데이터셋 정보:" )
    print(f" - 500자 이하 (70% 샘플링): {len(short_sample)}개")
    print(f" - 500~1000자 (25% 샘플링): {len(medium_sample)}개")
    print(f" - 1000자 초과 (5% 샘플링): {len(long_sample)}개")
    print(f"▶ 총 file_name 개수:  {len(final_filenames)}개")
    print(f"▶ 최종 데이터셋의 행 개수:  {len(final_df)}개")
    print("--------------------------------------------------")

    print("▶ 최종 데이터셋 미리보기 (상위 5개 행):\n" )
    print(final_df.head())


except FileNotFoundError:
    print(f"오류: '{file_path}' 파일을 찾을 수 없습니다.")
    print("파일 경로를 다시 확인해주세요.")
except Exception as e:
    print(f"작업 중 오류가 발생했습니다: {e}")

# --- 7. 최종 데이터셋을 CSV 파일로 저장 ---
output_csv_path = 'dataset/일반통화정제데이터셋.csv'
try:
    final_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f"\n▶ 최종 데이터셋이 ' {output_csv_path}' 파일로 성공적으로 저장되었습니다.")
except Exception as e:
    print(f"\n오류: 최종 데이터셋 저장 중 문제가 발생했습니다: {e}")