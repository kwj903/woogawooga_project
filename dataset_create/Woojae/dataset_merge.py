import pandas as pd
import os

# 이 스크립트 파일의 위치(dataset_create/Woojae)를 기준으로 상위 폴더로 이동하여   
# 프로젝트의 루트 디렉토리 경로를 계산합니다.
# os.path.dirname(__file__)는 현재 파일의 디렉토리 경로를 반환합니다.
# '..'는 상위 디렉토리를 의미합니다.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# 데이터셋 파일들이 있는 디렉토리 경로를 설정합니다.
dataset_dir = os.path.join(project_root, 'dataset')

# 병합할 파일들의 전체 경로 리스트를 만듭니다.
files_to_merge = [
    os.path.join(dataset_dir, '공감대화정제데이터셋.csv'),
    os.path.join(dataset_dir, '일반대화정제데이터셋.csv'),
    os.path.join(dataset_dir, '콜센터정제데이터셋.csv')
]

# 병합 후 저장될 파일의 전체 경로를 설정합니다.
output_file = os.path.join(dataset_dir, '일반통화대화통합.csv')  

# 각 파일을 읽어와 DataFrame으로 변환한 뒤, 리스트에 저장합니다.
df_list = []

for file in files_to_merge:
    try:
        # CSV 파일을 읽어옵니다.
        df = pd.read_csv(file)
        # 'spk' 컬럼은 'speaker'로, 'msg' 컬럼은 'text'로 이름을 변경합니다.
        df_renamed = df.rename(columns={'spk': 'speaker', 'msg': 'text'})
        # 처리된 DataFrame을 리스트에 추가합니다.
        df_list.append(df_renamed)
        print(f"성공적으로 파일을 읽고 컬럼명을 변경했습니다: {os.path.basename(file)}")
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {file}")
    except Exception as e:
        print(f"파일 처리 중 오류 발생 {file}: {e}")

# 리스트에 DataFrame이 하나 이상 있을 경우에만 병합을 진행합니다.
if df_list:
    # 리스트에 있는 모든 DataFrame을 하나로 병합합니다.
    # ignore_index=True는 기존 인덱스를 무시하고 새로운 인덱스를 생성하는 옵션입니다.
    merged_df = pd.concat(df_list, ignore_index=True)

    # 병합된 DataFrame을 새로운 CSV 파일로 저장합니다.
    # index=False는 DataFrame의 인덱스를 파일에 쓰지 않는 옵션입니다.
    # encoding='utf-8-sig'는 한글 깨짐을 방지하기 위한 설정입니다.
    merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n성공적으로 파일들을 병합하여 다음 경로에 저장했습니다: {output_file}")
else:
    print("\n병합할 파일이 없습니다.")