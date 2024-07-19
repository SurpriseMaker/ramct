import os
import re
import time
import pandas as pd
from show import Show

class LaunchInfoParser():
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
            output_txt_path = os.path.join(path, "launchinfo.txt")
            start_second = time.time()
            os.system(f"grep -ri MotoDisplayed --exclude={output_txt_path} {path}/*Stream-s*.* 1> {output_txt_path}")
            end_second = time.time()
            print(f"grep duration seconds={end_second - start_second}")
            launch_info_dict = LaunchInfoParser.get_launch_info(output_txt_path)
            data.update(launch_info_dict)
            data_list_all.append(data)
        
        return data_list_all
    
    @staticmethod
    def get_launch_info(txt_path):
        # format:  LaunchCheckinHandler: MotoDisplayed com.motorola.launcher3/com.android.launcher3.CustomizationPanelLauncher,wp,ca,2992
        df = pd.read_csv(txt_path, names=['col1', 'process_launch_type', 'activity_launch_type', 'duration'])
        data = {}
        total_launch_count = len(df.index)
        wp_count = len(df[df['process_launch_type']=='wp'].index)
        
        wp_ratio = float(wp_count)/total_launch_count
        data['warm_process_ratio'] = wp_ratio
        data['total_launch_count'] = total_launch_count
        data['warm_process_count'] = wp_count

        return data
    
    @staticmethod
    def get_launch_info_excel_path(dir):
        keyword = os.path.basename(dir)
        file_path = os.path.join(dir, f"{keyword}_launch_info.xlsx")
        return file_path
    
    @staticmethod
    def parse_launchinfo(log_path):
        pattern = r'\d{4}-\d{2}-\d{2}'
        path_list=LaunchInfoParser.get_all_log_paths(log_path, pattern)
        output_excel_path = LaunchInfoParser.get_launch_info_excel_path(log_path)
        data_list_all = LaunchInfoParser.grep_info(path_list)
        if data_list_all:
            df_all = (pd.DataFrame(data_list_all)).drop_duplicates()
            df_all.to_excel(output_excel_path, index=False)
        else:
            print("ops, check why launch info is empty.")
            output_excel_path = None
            
        return output_excel_path
    
if __name__ == '__main__':
    log_path = "D:/glory/rack/NZ4C240007"
    excel_path = LaunchInfoParser.parse_launchinfo(log_path)
    
    Show.draw_launch_info(log_path, excel_path)