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
    def read_lines(file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                yield line

    @staticmethod
    def parse_pss_data(dir: str):
            data = []
            pattern = re.compile(r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{3}\s+\d+\s+\d+\s+I\s+am_pss  : \[(\d+),(\d+),([^,]+),(\d+),\d+,\d+,(\d+)")

            for root, dirs, files in os.walk(dir):
                for file in files:
                    if 'Stream-e' in file or "event" in file or 'logcat' in file:
                        file_path = os.path.join(root, file)
                        #log.info(f"Parsing {file_path}")
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line in PssParser.read_lines(file_path):
                                match = pattern.search(line)
                                if match:
                                    data.append({
                                        'datetime' : match.group(1),
                                        'pid': int(match.group(2)),
                                        'uid': int(match.group(3)),
                                        'package': match.group(4),
                                        'pss': int(match.group(5))//1024 if int(match.group(5)) > 0 else int(match.group(6))//1024,
                                    })

            df = pd.DataFrame(data)
            log.info(f"df = {df}")
            if df.empty:
                log.warning("Not found any PSS data.")
                return None
            
            # 确保'datetime'列为日期时间格式
            df['datetime'] = pd.to_datetime(df['datetime'], format='%m-%d %H:%M:%S')
            df = df.sort_values('datetime')  # 按时间升序排序
            # new_df = df.pivot(columns='package', values='pss')
    
            # # 使用apply方法并行处理每一列，去除空值并填充到最长长度
            # cleaned_series = [new_df[col].dropna().reset_index(drop=True) for col in new_df.columns]

            # # 使用pd.concat将处理后的Series拼接成新的DataFrame
            # clean_df = pd.concat(cleaned_series, axis=1)

            excel_path = PssParser.get_output_excel_path(dir)
            if not df.empty:
                df.to_excel(excel_path, index=False)
                return excel_path
            else:
                log.warning("Not found any PSS data.")
                return None

if __name__ == "__main__":
    folder_path = "D:/github/ramct/downloads/NZ4C240007"
    PssParser.parse_pss_data(folder_path)
    excel_path = PssParser.get_output_excel_path(folder_path)
    if excel_path:
        Show.draw_initial_report(folder_path, 'Test')
        Show.draw_pss_report(folder_path, excel_path)