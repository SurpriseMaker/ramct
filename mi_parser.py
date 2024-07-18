import os
import re
import pandas as pd

class ParseMeminfo():
    @staticmethod
    def parseAndGetData(content):
        end_keyword = 'Total PSS by category'
        data = {}
        start_fetch = False
        for line in content:
            if end_keyword in line:
                break
            if start_fetch:
                # 53,690K: surfaceflinger (pid 1207)                                    (   11,980K in swap)
                pattern = r"(.+)K: (.+)"
                match = re.search(pattern, line)
                if match:
                    size_kb = int(match.group(1).replace(',', ''))
                    #print(f"match.group(1)={match.group(1)}, match.group(2)={match.group(2)}")
                    name = match.group(2).split('(')[0].replace(' ', '')
                    if not (name in data) :
                        data[name] = size_kb
                        #print(f"{name} --- {size_kb}")
            else:
                match = re.findall(r"Total PSS by OOM adjustment:", line)
                if match:
                    start_fetch = True
                    continue
        
        return data

    @staticmethod
    def get_all_dump_file_paths(file_path: str):
        paths = os.walk(file_path)
        found_file_path_list = []

        key = 'meminfo'
        for path, dir_lst, file_lst in paths:
            for file in file_lst:
                if file.find(key) != -1:
                    found = os.path.join(path, file)
                    found_file_path_list.append(found)
                    print(f"找到路径: {found}")

        return found_file_path_list

    @staticmethod
    def parseOneFile(file_path: str):
        file_name = os.path.basename(file_path)
        data = {'file_name':file_name}
        with open(file_path, "r") as f:
            content = f.readlines()
            data.update(ParseMeminfo.parseAndGetData(content))
        if data:
            pass
        else:
            print("No match")

        return data

    @staticmethod
    def parseAllFiles(dir, singal_progress=None):
        path_list=ParseMeminfo.get_all_dump_file_paths(dir)
        data_list_all = []
        for path in path_list:
            data = ParseMeminfo.parseOneFile(path)
            data_list_all.append(data)
            if singal_progress:
                singal_progress.emit(path)
        
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
            df_all.to_excel(excel_path, index=False)
        else:
            print("Not found any valuable meminfo! Please check if meminfo logs exists or not.")
            excel_path = None
        
        return excel_path

    def get_output_excel_path(dir):
        keyword = os.path.basename(dir)
        file_path = os.path.join(dir, f"{keyword}_meminfo.xlsx")
        return file_path

    @staticmethod 
    def parseMeminfos(**kwargs):
        print(f"kwargs = {kwargs}")
        singal_progress = kwargs['progress_callback']
        dir = kwargs['dir']

        return ParseMeminfo.parseAllFiles(dir, singal_progress)

if __name__ == '__main__':
    dir=os.getcwd()
    output_excel_path = ParseMeminfo.get_output_excel_path(dir)
    ParseMeminfo.parseAllFiles(dir)