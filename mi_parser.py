import os
import re
import fnmatch
import pandas as pd
from log_utils import log

class ParseMeminfo():
    @staticmethod
    def read_lines(file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                yield line

    @staticmethod
    def get_output_excel_path(dir):
        keyword = os.path.basename(dir)
        file_path = os.path.join(dir, f"{keyword}_mi.xlsx")
        return file_path

    @staticmethod
    def parse_one_file(file_path: str):
        file_name = os.path.basename(file_path)
        # 匹配日期时间部分
        match = re.search(r'_(\d{4}_\d{2}_\d{2}(?:_\d{2})?(?:_\d{2})?(?:_\d{2})?)\.txt$', file_name)
        if match:
            datetime_str = match.group(1)
            data = {'date_time':datetime_str}
        else:
            return None

        PATTERN_PSS_OOM = r"(.+)K: (.+)"
        PATTERN_RAM_CATEGORY = r"(.+):\s*([\d,]+)K"
        # keyword:  pattern
        keyword_pattern = {'Total PSS by OOM adjustment:'   : PATTERN_PSS_OOM,
                           'Total PSS by category'          : None,
                             'Total RAM:'                   : PATTERN_RAM_CATEGORY,
                             'Tuning: '                     : None}

        pattern = None
        for line in ParseMeminfo.read_lines(file_path):
            for keyword, pattern_info in keyword_pattern.items():
                if keyword in line:
                    pattern = pattern_info
                    break
            if pattern:
                match = re.search(pattern, line)
                if match:
                    # 53,690K: surfaceflinger (pid 1207)                                    (   11,980K in swap)
                    if pattern == PATTERN_PSS_OOM:
                        size_kb = int(match.group(1).replace(',', ''))
                        name = match.group(2).split('(')[0].replace(' ', '')[:40]
                        if name not in data:
                            data[name] = size_kb
                    elif pattern == PATTERN_RAM_CATEGORY:
                        name = match.group(1).strip()
                        size_kb = int(match.group(2).replace(',', ''))
                        if name not in data:
                            data[name] = size_kb
        
        if len(data) <= 1:
            log.info(f"No match found in the file: {file_path}")

        return data

    @staticmethod
    def parse_all_files(dir):
        try:
            data_list_all = []
            key = 'meminfo'
            for path, dir_lst, file_lst in os.walk(dir):
                for file in fnmatch.filter(file_lst, f'*{key}*'):
                    file_path = os.path.join(path, file)
                    try:
                        data = ParseMeminfo.parse_one_file(file_path)
                        if data:
                            data_list_all.append(data)

                    except Exception as e:
                        log.error(f"Error parsing file {file_path}: {e}")

            excel_path = ParseMeminfo.get_output_excel_path(dir)
            if data_list_all:
                df_all = (pd.DataFrame(data_list_all)).drop_duplicates()
                columns = list(df_all.columns)
                native_index = columns.index('Native')
                system_index = columns.index('Foreground')
                
                columns_to_sort = df_all.columns[(native_index + 1): (system_index -1)]

                print(f"columns_to_sort: {columns_to_sort}")
                # 按每列的最大值排序
                sorted_columns = sorted(columns_to_sort, key=lambda col: df_all[col].max(), reverse=False)
                
                # 重新排列这些列
                for col in sorted_columns:
                    columns.insert(native_index + 1, columns.pop(columns.index(col)))
                
                df_reindex = df_all.reindex(columns=columns)
                
                df_reindex['date_time'] = pd.to_datetime(df_reindex['date_time'], format='%Y_%m_%d_%H_%M_%S')
                if not df_reindex.empty:
                    df_reindex.to_excel(excel_path, index=False)
                else:
                    log.warning("All data entries were duplicates.")
            else:
                log.info("Not found any valuable meminfo! Please check if meminfo logs exists or not.")
                excel_path = None
        except Exception as e:
            log.error(f"Error processing files in directory {dir}: {e}")
            excel_path = None

        return excel_path


if __name__ == '__main__':
    dir=os.getcwd()
    output_excel_path = ParseMeminfo.get_output_excel_path(dir)
    ParseMeminfo.parse_all_files(dir)