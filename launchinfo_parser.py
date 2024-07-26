import os
import re
import time
import logging
import subprocess
import pandas as pd
from show import Show

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='ramct.log')
class LaunchInfoParser():
    @staticmethod
    def get_all_log_paths(file_path: str, pattern):
        found_path_list = []

        for path, dir_lst, file_lst in os.walk(file_path):
            for dir_name  in dir_lst:
                if re.search(pattern, dir_name):
                    found_path_list.append(os.path.join(path, dir_name))

        for found in found_path_list:
            logging.info(f"找到路径: {found}")
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
                logging.info(f"grep duration seconds={end_second - start_second}")
                
                launch_info_dict = LaunchInfoParser.get_launch_info(output_txt_path)
                data.update(launch_info_dict)
                data_list_all.append(data)
            
            except subprocess.CalledProcessError as e:
                logging.info(f"Error executing grep command: {e}")
            except Exception as e:
                logging.info(f"An error occurred: {e}")
        
        return data_list_all
    
    @staticmethod
    def get_launch_info(txt_path):
        # format:  LaunchCheckinHandler: MotoDisplayed com.motorola.launcher3/com.android.launcher3.CustomizationPanelLauncher,wp,ca,2992
        try:
            # Read the CSV file with specified column names
            df = pd.read_csv(txt_path, names=['col1', 'process_launch_type', 'activity_launch_type', 'duration'])
        except FileNotFoundError:
            logging.error(f"The file at {txt_path} was not found.")
            return None
        except pd.errors.ParserError:
            logging.error(f"The file at {txt_path} is not a valid CSV file.")
            return None

        data = {}
        total_launch_count = len(df.index)
        if total_launch_count == 0:
            logging.warning("The file is empty or contains no rows.")
            data['warm_process_ratio'] = 0.0
            data['total_launch_count'] = 0
            data['warm_process_count'] = 0
            return data
        else:
            try:
                wp_count = len(df[df['process_launch_type'] == 'wp'].index)
                wp_ratio = float(wp_count) / total_launch_count
            except KeyError:
                logging.error("The 'process_launch_type' column is missing or incorrectly named.")
                return None
            except TypeError:
                logging.error("The 'process_launch_type' column contains unexpected data types.")
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
    
    @staticmethod
    def parse_launchinfo(log_path):
        try:
            pattern = r'\d{4}-\d{2}-\d{2}'
            path_list=LaunchInfoParser.get_all_log_paths(log_path, pattern)
            if not path_list:
                    logging.warning("No log paths found.")
                    return None
            output_excel_path = LaunchInfoParser.get_launch_info_excel_path(log_path)
            data_list_all = LaunchInfoParser.grep_info(path_list)
            if not data_list_all:
                    logging.warning("Ops, check why launch info is empty.")
                    return None

            df_all = (pd.DataFrame(data_list_all)).drop_duplicates()
            if df_all.empty:
                    logging.warning("All data are duplicates.")
                    return None

            try:
                df_all.to_excel(output_excel_path, index=False)
            except Exception as e:
                logging.error(f"Failed to write Excel file: {e}")
                return None


            return output_excel_path
        
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return None
    
if __name__ == '__main__':
    log_path = "D:/glory/rack/NZ4C240007"
    excel_path = LaunchInfoParser.parse_launchinfo(log_path)
    
    Show.draw_launch_info(log_path, excel_path)