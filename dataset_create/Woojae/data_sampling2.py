import pandas as pd

# --- 1. 파일 불러오기 ---
try:
    # 파일 경로 지정
    file_path = 'dataset/normal_dataset(콜센터).csv'
    # CSV 파일을 DataFrame으로 읽어오기 (encoding을 'utf-8'로 지정)
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"'{file_path}' 파일을 성공적으로 불러왔습니다. (총 {len(df)}개 행)")
    print("-" * 50)
  
    # --- 2. file_name 기준으로 msg 길이 계산 ---
    print("file_name 별로 메시지 길이를 계산합니다...")
    msg_lengths = df.groupby('file_name')['msg'].apply(lambda x: len(''.join(str(s) for s in x)))
    print("-" * 50)

    # --- 3. 1000자 이하 데이터 개수 구하기 ---
    count_under_1000 = msg_lengths[msg_lengths <= 1000].shape[0]
    print(f"▶ 메시지 총 길이가 1000자 이하인 데이터(file_name 기준)의 개수:  {count_under_1000}개")
    print("--------------------------------------------------")

    # --- 4. & 5. 글자 길이 기준으로 데이터셋 샘플링 (수정된 로직) ---
    print("글자 길이 기준으로 데이터셋을 샘플링합니다 (최종 5000개 이상 목표)...\n")

    # 각 길이 그룹별로 file_name 리스트 생성
    short_files = msg_lengths[msg_lengths <= 500].index
    medium_files = msg_lengths[(msg_lengths > 500) & (msg_lengths <= 1000)].index
    long_files = msg_lengths[msg_lengths > 1000].index

    # 목표 개수 설정
    target_total_files = 10000 # 사용자 요청: 5000개 이상
    target_short_count = int(target_total_files * 0.70)
    target_medium_count = int(target_total_files * 0.25)
    target_long_count = int(target_total_files * 0.05)

    # 각 그룹에서 목표 개수만큼 샘플링 (random_state는 재현성을 위해 고정)
    # 만약 목표 개수보다 실제 데이터가 적으면, 가능한 모든 데이터를 추출
    short_sample = short_files.to_series().sample(n=min(len(short_files), target_short_count), random_state=42)
    medium_sample = medium_files.to_series().sample(n=min(len(medium_files), target_medium_count), random_state=42)
    long_sample = long_files.to_series().sample(n=min(len(long_files), target_long_count), random_state=42)

    # 샘플링된 file_name들을 하나로 합치기
    final_filenames = pd.concat([short_sample, medium_sample, long_sample]).index

    # --- 6. 최종 데이터셋 생성 ---\n
    final_df = df[df['file_name'].isin(final_filenames)].reset_index(drop=True)

    print("▶ 최종 샘플링된 데이터셋 정보:" )
    print(f" - 500자 이하 (목표 {target_short_count}개): 실제 샘플링 {len(short_sample)}개")
    print(f" - 500~1000자 (목표 {target_medium_count}개): 실제 샘플링 {len(medium_sample)}개")
    print(f" - 1000자 초과 (목표 {target_long_count}개): 실제 샘플링 {len(long_sample)}개")
    print(f"▶ 총 file_name 개수:  {len(final_filenames)}개")
    print(f"▶ 최종 데이터셋의 행 개수:  {len(final_df)}개")
    print("--------------------------------------------------")

    print("▶ 최종 데이터셋 미리보기 (상위 5개 행):\n" )
    print(final_df.head())

    # --- 7. 최종 데이터셋을 CSV 파일로 저장 ---
    output_csv_path = 'dataset/콜센터정제데이터셋2.csv'
    try:
        final_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
        print(f"\n▶ 최종 데이터셋이 ' {output_csv_path}' 파일로 성공적으로 저장되었습니다.")
    except Exception as e:
        print(f"\n오류: 최종 데이터셋 저장 중 문제가 발생했습니다: {e}")
  
except FileNotFoundError:
    print(f"오류: '{file_path}' 파일을 찾을 수 없습니다.")
    print("파일 경로를 다시 확인해주세요.")
except Exception as e:
    print(f"작업 중 오류가 발생했습니다: {e}")