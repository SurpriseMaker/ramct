import os
import re
import pandas as pd
from log_utils import log
from show import Show

class CpuParser():
    @staticmethod
    def get_output_excel_path(dir):
            keyword = os.path.basename(dir)
            file_path = os.path.join(dir, f"{keyword}_cpu.xlsx")
            return file_path

    @staticmethod
    def read_lines(file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                yield line
            
    @staticmethod
    def parse_cpu_data(dir: str):
            data_list = []
            data = {}
            # 08-17 04:56:09.163  1953  2750 I ActivityManager:
            pattern = re.compile(r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{3}\s+\d+\s+\d+\s+I\s+ActivityManager:\s+(\d+)% \d+/(\S+):")

            for root, dirs, files in os.walk(dir):
                for file in files:
                    if 'Stream-s' in file:
                        file_path = os.path.join(root, file)
                        log.info(f"Parsing {file_path}")
                        for line in CpuParser.read_lines(file_path):
                            match = pattern.search(line)
                            if match:
                                date_time = match.group(1)
                                cpu_percent = int(match.group(2))
                                process_name = match.group(3)
                                if date_time not in data:
                                    if data:
                                        data_list.append(data)
                                    data = {'date_time': date_time}
                                data[process_name] = cpu_percent

            # 最后一个数据也要添加到列表中
            if data!= {}:
                data_list.append(data)
            # 转换为DataFrame
            df = pd.DataFrame(data_list)
            log.info(f"df = {df}")
            if df.empty:
                log.warning("Not found any CPU data.")
                return None

            df['date_time'] = pd.to_datetime(df['date_time'], format='%m-%d %H:%M:%S')
            # 保存到Excel文件
            excel_path = CpuParser.get_output_excel_path(dir)
            log.info(f"Saving CPU data to {excel_path}")
            df.to_excel(excel_path, index=False)
            log.info("Saved")
            return excel_path

if __name__ == "__main__":
    folder_path = "D:/github/ramct/downloads/NFNAX10114"
    excel_path =CpuParser.parse_cpu_data(folder_path)
    if excel_path:
        Show.draw_initial_report(folder_path, 'CPU_Test')
        Show.draw_cpu_report(folder_path, excel_path)