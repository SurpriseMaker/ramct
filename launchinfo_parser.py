import os
import re
import time
import subprocess
import pandas as pd
from show import Show
from log_utils import log

class LaunchInfoParser():
    @staticmethod
    def get_all_log_paths(file_path: str, pattern):
        found_path_list = []

        for path, dir_lst, file_lst in os.walk(file_path):
            for dir_name  in dir_lst:
                if re.search(pattern, dir_name):
                    found_path_list.append(os.path.join(path, dir_name))

        for found in found_path_list:
            log.info(f"找到路径: {found}")
        return found_path_list
    
    @staticmethod
    def grep_info(path_list):
        data_list_all = []
        for path in path_list:
            data = {'dir_name':os.path.basename(path)}
            output_txt_path = os.path.join(path, "launchinfo.txt")
            start_second = time.time()
            try:
                # Use subprocess to run the grep command
                result = subprocess.run(
                    ["grep", "-ri", "MotoDisplayed", "--exclude=" 
                     + output_txt_path, os.path.join(path, "*Stream-s*.*")],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
                with open(output_txt_path, 'w') as f:
                    f.write(result.stdout)
                
                end_second = time.time()
                log.info(f"grep duration seconds={end_second - start_second}")
                
                launch_info_dict = LaunchInfoParser.get_launch_info(output_txt_path)
                data.update(launch_info_dict)
                data_list_all.append(data)
            
            except subprocess.CalledProcessError as e:
                log.info(f"Error executing grep command: {e}")
            except Exception as e:
                log.info(f"An error occurred: {e}")
        
        return data_list_all
    
    @staticmethod
    def get_launch_info(txt_path):
        # format:  LaunchCheckinHandler: MotoDisplayed com.motorola.launcher3/com.android.launcher3.CustomizationPanelLauncher,wp,ca,2992
        try:
            # Read the CSV file with specified column names
            df = pd.read_csv(txt_path, names=['col1', 'process_launch_type', 'activity_launch_type', 'duration'])
        except FileNotFoundError:
            log.error(f"The file at {txt_path} was not found.")
            return None
        except pd.errors.ParserError:
            log.error(f"The file at {txt_path} is not a valid CSV file.")
            return None

        data = {}
        total_launch_count = len(df.index)
        if total_launch_count == 0:
            log.warning("The file is empty or contains no rows.")
            data['warm_process_ratio'] = 0.0
            data['total_launch_count'] = 0
            data['warm_process_count'] = 0
            return data
        else:
            try:
                wp_count = len(df[df['process_launch_type'] == 'wp'].index)
                wp_ratio = float(wp_count) / total_launch_count
            except KeyError:
                log.error("The 'process_launch_type' column is missing or incorrectly named.")
                return None
            except TypeError:
                log.error("The 'process_launch_type' column contains unexpected data types.")
                return None

        data['warm_process_ratio'] = wp_ratio
        data['total_launch_count'] = total_launch_count
        data['warm_process_count'] = wp_count

        return data
    
    @staticmethod
    def get_launch_info_excel_path(dir):
        keyword = os.path.basename(dir)
        file_path = os.path.join(dir, f"{keyword}_launch_info.xlsx")
        return file_path
    
    # @staticmethod
    # def parse_launchinfo(log_path):
    #     try:
    #         pattern = r'\d{4}-\d{2}-\d{2}'
    #         path_list=LaunchInfoParser.get_all_log_paths(log_path, pattern)
    #         if not path_list:
    #                 log.warning("No log paths found.")
    #                 return None
    #         output_excel_path = LaunchInfoParser.get_launch_info_excel_path(log_path)
    #         data_list_all = LaunchInfoParser.grep_info(path_list)
    #         if not data_list_all:
    #                 log.warning("Ops, check why launch info is empty.")
    #                 return None

    #         df_all = (pd.DataFrame(data_list_all)).drop_duplicates()
    #         if df_all.empty:
    #                 log.warning("All data are duplicates.")
    #                 return None

    #         try:
    #             df_all.to_excel(output_excel_path, index=False)
    #         except Exception as e:
    #             log.error(f"Failed to write Excel file: {e}")
    #             return None


    #         return output_excel_path
        
    #     except Exception as e:
    #         log.error(f"An error occurred: {e}")
    #         return None
        
    @staticmethod
    def parse_launchinfo(dir):
        output_excel_path = None
        data_list = []
        
        #08-03 11:53:46.077  1784  2473 I LaunchCheckinHandler: MotoDisplayed com.google.android.dialer/com.android.dialer.incall.activity.ui.InCallActivity,wp,ca,261
        pattern = r"(\d{2}-\d{2}) \d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+I\s+LaunchCheckinHandler: MotoDisplayed [^,]+\,(\w+)\,(\w+)\,(\d+)"
        for root, dirs, files in os.walk(dir):
            for file in files:
                if 'Stream-s' in file:
                    file_path = os.path.join(root, file)
                    #log.info(f"Parsing {file_path}")
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        matches = re.findall(pattern, content)
                        for match in matches:
                            data_list.append({
                                'date': match[0],
                                'process_launch_type': match[1],
                                'activity_launch_type': match[2],
                                'duration': match[3]
                            })
        
        df = pd.DataFrame(data_list)
        
        if df.empty:
            log.warning("Not found any killing data.")
            return None
        
        log.info(f"df = {df}")

        # 按日期统计总行数
        total_counts = df.groupby('date').size().reset_index(name='total_count')
        
        # 按日期统计process_launch_type列中值为wp的个数
        wp_counts = df[df['process_launch_type'] == 'wp'].groupby('date').size().reset_index(name='wp_count')
        
        # 合并总行数和wp的个数
        result = pd.merge(total_counts, wp_counts, on='date', how='left').fillna(0)
        # 计算wp的比例
        result['wp_ratio'] = result['wp_count'] / result['total_count']
        
        # 确保列顺序为 date, wp_ratio, wp_count, total_count
        result = result[['date', 'wp_ratio', 'wp_count', 'total_count']]
        
        # 将日期字符串转换为日期类型
        result['date'] = pd.to_datetime(result['date'], format='%m-%d')
        if not result.empty:
            # 保存结果到excel文件
            output_excel_path = LaunchInfoParser.get_launch_info_excel_path(dir)
            result.to_excel(output_excel_path, index=False)
        else:
            log.warning("Not found any launch info data.")
            
        return output_excel_path

if __name__ == '__main__':
    log_path = "D:/glory/rack/NZ4C240007"
    excel_path = LaunchInfoParser.parse_launchinfo(log_path)
    
    Show.draw_launch_info(log_path, excel_path)