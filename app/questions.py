import pandas as pd
import re

file_path = "questions.xlsx"

def extract_questions(file_path):
    # 엑셀 파일 불러오기
    xls = pd.ExcelFile(file_path)
    sheet_names = xls.sheet_names[1:]  # 첫 번째 시트 제외

    data_list = []
    id_idx=0
    
    for sheet in sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)

        # 컬럼명 표준화 (실제 컬럼명을 확인 후 수정 필요)
        df.columns = [col.strip() for col in df.columns]

        # 필요한 컬럼만 선택 (컬럼명이 다를 경우 수정 필요)
        required_columns = ['지문유형', '문항명', '정답', '난이도', '지문']
        excel_df = df[[col for col in required_columns if col in df.columns]]
        

        for idx, row in excel_df.iterrows():
            # 기본 컬럼 매핑
            question_id = id_idx + 1  # ID 자동 증가 (엑셀에서 별도 ID 없을 경우)
            subject = sheet.split("_")[0].strip()
            if row['지문유형'] == '객관식':
                question_type = '객관식'
            else:
                question_type = '주관식'
            text = row['문항명']
            answer = str(row['정답'])
            difficulty = row['난이도']
            optext = row['지문']

            # 객관식인 경우 op1~op5 설정
            options=[None]*5
            if question_type == '객관식':
                option_list = re.split(r'\n| {3,}', optext)[:5]
                for i in range(5):
                    options[i] = str(option_list[i]).strip()
                    

            # 변환된 데이터를 리스트에 추가
            data_list.append({
                'id': question_id,
                'subject': subject,
                'type': question_type,
                'text': text,
                'answer': answer,
                'diff': difficulty,
                'op1': options[0],
                'op2': options[1],
                'op3': options[2],
                'op4': options[3],
                'op5': options[4],
            })
            id_idx += 1

    # 리스트를 DataFrame으로 변환
    transformed_df = pd.DataFrame(data_list)

    return transformed_df
