import os
import re
import pandas as pd
from show import Show

module_path = os.path.dirname(os.path.abspath(__file__))
grep_exe = f"{module_path}/grep/grep.exe"

class KillinfoParser():
    @staticmethod
    def get_all_log_paths(file_path: str, pattern):
        paths = os.walk(file_path)
        found_path_list = []

        for path, dir_lst, file_lst in paths:
            for dir in dir_lst:
                match = re.search(pattern, dir)
                if match:
                    found = os.path.join(path, dir)
                    found_path_list.append(found)
                    print(f"找到路径: {found}")

        return found_path_list
    
    @staticmethod
    def grep_info(path_list):
        data_list_all = []
        for path in path_list:
            data = {'dir_name':os.path.basename(path)}
            output_txt_path = os.path.join(path, "killinfo.txt")
            os.system(f"{grep_exe} -ri killinfo --exclude=killinfo.txt {path} 1> {output_txt_path}")
            with open(output_txt_path, "r") as f:
                content = f.readlines()
                kill_count_dict = KillinfoParser.get_kill_count(content)
                data.update(kill_count_dict)
                data_list_all.append(data)
        
        return data_list_all
    
    @staticmethod
    def get_kill_count(content):
        heavy_kill_count = 0
        critical_kill_count = 0
        medium_kill_count = 0
        data = {}
        for line in content:
            pattern = r"killinfo: \[(\d+)\,(\d+)\,(\d+)\,"
            match = re.search(pattern, line)
            if match:
                killed_adj = int(match.group(3))
                if killed_adj < 201:
                    heavy_kill_count += 1
                elif killed_adj < 920:
                    critical_kill_count += 1
                else:
                    medium_kill_count += 1
                    
        data['heavy_kill'] = heavy_kill_count
        data['critical_kill'] = critical_kill_count
        data['medium_kill'] = medium_kill_count
        return data

    @staticmethod
    def get_killinfo_output_excel_path(dir):
        keyword = os.path.basename(dir)
        file_path = os.path.join(dir,
                                       f"{keyword}_output.xlsx")
        return file_path

    def parse_killinfo(log_path):
        pattern = r'\d{4}-\d{2}-\d{2}'
        path_list=KillinfoParser.get_all_log_paths(log_path, pattern)
        killinfo_output_excel_path = KillinfoParser.get_killinfo_output_excel_path(log_path)
        data_list_all = KillinfoParser.grep_info(path_list)
        if data_list_all:
            df_all = (pd.DataFrame(data_list_all)).drop_duplicates()
            df_all.to_excel(killinfo_output_excel_path, index=False)
        else:
            print("ops, check why data list is empty.")
            
        return killinfo_output_excel_path

if __name__ == '__main__':
    log_path = "D:/下载/NFNAX10115Logger.tar/NFNAX10115Logger"
    killinfo_output_excel_path = KillinfoParser.parse_killinfo(log_path)
    
    Show.draw_killing(log_path, killinfo_output_excel_path)