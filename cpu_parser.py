import os
import re
import pandas as pd
from tqdm import tqdm
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
            # 08-11 23:48:36.443  1903  2548 I ActivityManager: 25% TOTAL: 12% user + 10% kernel + 0.2% iowait + 1.4% irq + 0.2% softirq
            pattern1 = re.compile(r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{3}\s+\d+\s+\d+\s+I\s+ActivityManager:\s+(\d+\.?\d?)% TOTAL:\s+(\d+\.?\d?)% user\s+\+\s+(\d+\.?\d?)% kernel\s+\+\s+(\d+\.?\d?)%\s+iowait")
            # 09-15 13:41:42.204  2439  2857 I ActivityManager:   87% 9727/com.tencent.mm: 59% user + 27% kernel / faults: 32766 minor 5353 major
            pattern2 = re.compile(r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{3}\s+\d+\s+\d+\s+I\s+ActivityManager:\s+(\d+)% \d+/(\S+):")

            for root, dirs, files in os.walk(dir):
                for file in tqdm(files, desc="Processing files", unit="file"):
                    if 'Stream-s' in file or 'system' in file:
                        file_path = os.path.join(root, file)
                        for line in tqdm(CpuParser.read_lines(file_path), desc=f"Reading {file}", unit="line"):
                            match1 = pattern1.search(line)
                            if match1:
                                date_time = match1.group(1)
                                total_percent = float(match1.group(2))
                                user_percent = float(match1.group(3))
                                kernel_percent = float(match1.group(4))
                                iowait_percent = float(match1.group(5))
                                if date_time not in data:
                                    if data:
                                        data_list.append(data)
                                    data = {'date_time': date_time}
                                data['total'] = total_percent
                                data['user'] = user_percent
                                data['kernel'] = kernel_percent
                                data['iowait'] = iowait_percent
                            match2 = pattern2.search(line)
                            if match2:
                                date_time = match2.group(1)
                                cpu_percent = float(match2.group(2))
                                process_name = match2.group(3)
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