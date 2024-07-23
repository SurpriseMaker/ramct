import os
import re
import fnmatch
import logging
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='ramct.log')
class ParseMeminfo():
    @staticmethod
    def parse_and_get_data(content):
        end_keyword = 'Total PSS by category'
        data = {}
        start_fetch = False
        # 53,690K: surfaceflinger (pid 1207)                                    (   11,980K in swap)
        pattern = r"(.+)K: (.+)"
        for line in content:
            if end_keyword in line:
                break
            if start_fetch:
                match = re.search(pattern, line)
                if match:
                    size_kb = int(match.group(1).replace(',', ''))
                    name = match.group(2).split('(')[0].replace(' ', '')
                    if name not in data:
                        data[name] = size_kb
            else:
                if "Total PSS by OOM adjustment:" in line:
                    start_fetch = True
        
        return data

    @staticmethod
    def get_all_dump_file_paths(file_path: str):
        found_file_path_list = []

        key = 'meminfo'
        for path, dir_lst, file_lst in os.walk(file_path):
            for file in fnmatch.filter(file_lst, f'*{key}*'):
                found = os.path.join(path, file)
                found_file_path_list.append(found)
                logging.info(f"找到路径: {found}")

        return found_file_path_list

    @staticmethod
    def parse_one_file(file_path: str):
        file_name = os.path.basename(file_path)
        data = {'file_name':file_name}

        try:
            with open(file_path, "r") as f:
                content = f.readlines()
        except FileNotFoundError:
            logging.error(f"File not found: {file_path}")
            return None
        except IOError as e:
            logging.error(f"Error reading file: {file_path}, {e}")
            return None
        
        parsed_data = ParseMeminfo.parse_and_get_data(content)
        if parsed_data:
            data.update(parsed_data)
        else:
            logging.info(f"No match found in the file: {file_path}")

        return data

    @staticmethod
    def parse_all_files(dir, singal_progress=None):
        try:
            path_list=ParseMeminfo.get_all_dump_file_paths(dir)
            data_list_all = []
            for path in path_list:
                try:
                    data = ParseMeminfo.parse_one_file(path)
                    data_list_all.append(data)
                    if singal_progress:
                        singal_progress.emit(path)
                except Exception as e:
                    logging.error(f"Error parsing file {path}: {e}")

            excel_path = ParseMeminfo.get_output_excel_path(dir)
            if data_list_all:
                df_all = (pd.DataFrame(data_list_all)).drop_duplicates()
                # columns = list(df_all)
                # columns.insert(1, columns.pop(columns.index('Perceptible')))
                # columns.insert(1, columns.pop(columns.index('Visible')))
                # columns.insert(1, columns.pop(columns.index('Foreground')))
                # columns.insert(1, columns.pop(columns.index('PersistentService')))
                # columns.insert(1, columns.pop(columns.index('Persistent')))
                # columns.insert(1, columns.pop(columns.index('System')))
                # columns.insert(1, columns.pop(columns.index('Native')))
                # df_reindex = df_all.reindex(columns=columns)
                if not df_all.empty:
                    df_all.to_excel(excel_path, index=False)
                else:
                    logging.warning("All data entries were duplicates.")
            else:
                logging.info("Not found any valuable meminfo! Please check if meminfo logs exists or not.")
                excel_path = None
        except Exception as e:
            logging.error(f"Error processing files in directory {dir}: {e}")
            excel_path = None

        return excel_path

    @staticmethod
    def get_output_excel_path(dir):
        keyword = os.path.basename(dir)
        file_path = os.path.join(dir, f"{keyword}_mi.xlsx")
        return file_path


if __name__ == '__main__':
    dir=os.getcwd()
    output_excel_path = ParseMeminfo.get_output_excel_path(dir)
    ParseMeminfo.parse_all_files(dir)