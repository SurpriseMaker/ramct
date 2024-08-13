import os
import re
import pandas as pd
from log_utils import log
from show import Show

class PssParser():
    @staticmethod
    def get_output_excel_path(dir):
            keyword = os.path.basename(dir)
            file_path = os.path.join(dir, f"{keyword}_pss.xlsx")
            return file_path

    @staticmethod
    def parse_pss_data(dir: str):
            data = []
            pattern = r"am_pss  : \[(\d+),(\d+),([^,]+),(\d+),"

            for root, dirs, files in os.walk(dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    log.info(f"Parsing {file_path}")
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        matches = re.findall(pattern, content)
                        for match in matches:
                            data.append({
                                'pid': int(match[0]),
                                'uid': int(match[1]),
                                'package': match[2],
                                'pss': int(int(match[3])/1024)
                            })

            df = pd.DataFrame(data)
            log.info(f"df = {df}")
            if df.empty:
                log.warning("Not found any PSS data.")
                return None
            new_df = df.pivot(columns='package', values='pss')
    
            # 使用apply方法并行处理每一列，去除空值并填充到最长长度
            cleaned_series = [new_df[col].dropna().reset_index(drop=True) for col in new_df.columns]

            # 使用pd.concat将处理后的Series拼接成新的DataFrame
            clean_df = pd.concat(cleaned_series, axis=1)

            excel_path = PssParser.get_output_excel_path(dir)
            if not clean_df.empty:
                clean_df.to_excel(excel_path, index=False)
                return excel_path
            else:
                log.warning("Not found any PSS data.")
                return None

if __name__ == "__main__":
    folder_path = "D:/github/ramct/downloads/NZ4C240007"
    PssParser.parse_pss_data(folder_path)
    excel_path = PssParser.get_output_excel_path(folder_path)
    Show.draw_initial_report(folder_path, 'Test')
    Show.draw_pss_report(folder_path, excel_path)