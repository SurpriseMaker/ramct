import os
import re
import pandas as pd
from show import Show
import time

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
            start_second = time.time()
            os.system(f"grep -ri killinfo --exclude=killinfo.txt {path}/*Stream-e*.* 1> {output_txt_path}")
            end_second = time.time()
            print(f"grep duration seconds={end_second - start_second}")
            with open(output_txt_path, "r") as f:
                content = f.readlines()
                start_second = time.time()
                kill_info_dict = KillinfoParser.get_kill_info(content)
                end_second = time.time()
                print(f"get_kill_info duration seconds={end_second - start_second}")
                data.update(kill_info_dict)
                data_list_all.append(data)
        
        return data_list_all
    
    @staticmethod
    def get_kill_info(content):
        heavy_kill_count = 0
        critical_kill_count = 0
        medium_kill_count = 0
        kill_depth = int(1000)
        mempsi_some_max = 0
        mempsi_full_max = 0
        iopsi_some_max = 0
        iopsi_full_max = 0
        cpupsi_max = 0
        data = {}
        for line in content:
            pattern = r"killinfo: \[(\d+)\,(\d+)\,(\d+)\,"
            match = re.search(pattern, line)
            if match:
                killed_adj = int(match.group(3))
                kill_depth = min(kill_depth, killed_adj)
                if killed_adj < 201:
                    heavy_kill_count += 1
                elif killed_adj < 920:
                    critical_kill_count += 1
                else:
                    medium_kill_count += 1
                    
            pattern2 = r"(\d+\.\d+)\,(\d+\.\d+)\,(\d+\.\d+)\,(\d+\.\d+)\,(\d+\.\d+)\]"
            match2 = re.search(pattern2, line)
            if match2:
                mempsi_some = float(match2.group(1))
                mempsi_some_max = max(mempsi_some_max, mempsi_some)
                mempsi_full = float(match2.group(2))
                mempsi_full_max = max(mempsi_full_max, mempsi_full)
                iopsi_some = float(match2.group(3))
                iopsi_some_max = max(iopsi_some_max, iopsi_some)
                iopsi_full = float(match2.group(4))
                iopsi_full_max = max(iopsi_full_max, iopsi_full)
                cpupsi = float(match2.group(5))
                cpupsi_max = max(cpupsi_max, cpupsi)
                    
        data['heavy_kill'] = heavy_kill_count
        data['critical_kill'] = critical_kill_count
        data['medium_kill'] = medium_kill_count
        data['kill_depth'] = kill_depth
        data['mempsi_some_max'] = mempsi_some_max
        data['mempsi_full_max'] = mempsi_full_max
        data['iopsi_some_max'] = iopsi_some_max
        data['iopsi_full_max'] = iopsi_full_max
        data['cpupsi_max'] = cpupsi_max
        return data

    @staticmethod
    def get_killinfo_output_excel_path(dir):
        keyword = os.path.basename(dir)
        file_path = os.path.join(dir, f"{keyword}_killinfo.xlsx")
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
            print("ops, check why kill info is empty.")
            killinfo_output_excel_path = None
            
        return killinfo_output_excel_path

if __name__ == '__main__':
    log_path = "D:/下载/NFNAX10115Logger.tar/NFNAX10115Logger"
    killinfo_output_excel_path = KillinfoParser.parse_killinfo(log_path)
    
    Show.draw_killing(log_path, killinfo_output_excel_path)