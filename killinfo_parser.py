import os
import re
import pandas as pd
from show import Show
import time
from log_utils import log

# 定义PROCESS_STATE的映射字典
PROCESS_STATE_MAP = {
    -1: "PROCESS_STATE_UNKNOWN",
    0: "PROCESS_STATE_PERSISTENT",
    1: "PROCESS_STATE_PERSISTENT_UI",
    2: "PROCESS_STATE_TOP",
    3: "PROCESS_STATE_BOUND_TOP",
    4: "PROCESS_STATE_FOREGROUND_SERVICE",
    5: "PROCESS_STATE_BOUND_FOREGROUND_SERVICE",
    6: "PROCESS_STATE_IMPORTANT_FOREGROUND",
    7: "PROCESS_STATE_IMPORTANT_BACKGROUND",
    8: "PROCESS_STATE_TRANSIENT_BACKGROUND",
    9: "PROCESS_STATE_BACKUP",
    10: "PROCESS_STATE_SERVICE",
    11: "PROCESS_STATE_RECEIVER",
    12: "PROCESS_STATE_TOP_SLEEPING",
    13: "PROCESS_STATE_HEAVY_WEIGHT",
    14: "PROCESS_STATE_HOME",
    15: "PROCESS_STATE_LAST_ACTIVITY",
    16: "PROCESS_STATE_CACHED_ACTIVITY",
    17: "PROCESS_STATE_CACHED_ACTIVITY_CLIENT",
    18: "PROCESS_STATE_CACHED_RECENT",
    19: "PROCESS_STATE_CACHED_EMPTY"
}

class KillinfoParser():
    @staticmethod
    def int_to_process_state(value):
        return PROCESS_STATE_MAP.get(value, "UNKNOWN_STATE")

    @staticmethod
    def get_killinfo_output_excel_path(dir):
        return os.path.join(dir, 'killinfo.xlsx')

    @staticmethod
    def read_lines(file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                yield line

    @staticmethod
    def parse_killinfo(dir):
        killinfo_output_excel_path = None
        data_list = []
        #01-18 17:13:33.654   723   723 I killinfo: [23908,10448,915,201,173576,14,93812,638636,34000,1436,53000,4288,2664712,478784,584484,540460,211764,374244,84116,332916,88448,119632,0,0,840,1016,104,11,0,29268,254540,5,10,2.730000,1.010000,3.010000,0.650000,11.110000]

        #pattern = r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{3}\s+\d+\s+\d+\s+I\s+killinfo:\s+\[\d+\,\d+\,(\d+)\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,(\d+\.\d+)\,(\d+\.\d+)\,(\d+\.\d+)\,(\d+\.\d+)\,(\d+\.\d+)\]"
        pattern = re.compile(r"(\d{2}-\d{2}) \d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+I\s+killinfo:\s+\[\d+\,\d+\,(\d+)\,.*")
        for root, dirs, files in os.walk(dir):
            for file in files:
                if 'Stream-e' in file:
                    file_path = os.path.join(root, file)
                    #log.info(f"Parsing {file_path}")
                    for line in KillinfoParser.read_lines(file_path):
                        match = pattern.search(line)
                        if match:
                            data_list.append({
                                'date': match.group(1),
                                'killed_adj': int(match.group(2)),
                            })
        
        df = pd.DataFrame(data_list)
        
        if df.empty:
            log.warning("Not found any killing data.")
            return None
        
        log.info(f"df = {df}")

        # 使用pd.cut将killed_adj列分箱
        bins = [0, 201, 921, float('inf')]
        labels = ['heavy_kill', 'critical_kill', 'medium_kill']
        df['killed_adj_bin'] = pd.cut(df['killed_adj'], bins=bins, labels=labels, right=False)
        
        # 按日期和分箱结果分组并统计个数
        grouped = df.groupby(['date', 'killed_adj_bin']).size().unstack(fill_value=0)
        
        # 重命名列
        grouped.columns = ['heavy_kill', 'critical_kill', 'medium_kill']
        
        # 将索引转换为列
        grouped.reset_index(inplace=True)
        
        # 将日期字符串转换为日期类型
        grouped['date'] = pd.to_datetime(grouped['date'], format='%m-%d')
        
        # 增加一列 heavy_kill_per_hour
        grouped['heavy_kill_per_hour'] = grouped['heavy_kill'] / 24
        
        # 移动 heavy_kill_per_hour 列到 date 列之后
        grouped = grouped[['date', 'heavy_kill_per_hour','heavy_kill', 'critical_kill','medium_kill']]

        # 打印每个日期的统计结果
        for _, row in grouped.iterrows():
            log.info(f"Date: {row['date']}")
            log.info(f"Counts: {row[['heavy_kill', 'critical_kill', 'medium_kill']].to_dict()}")
            
        if not grouped.empty:
            # 保存结果到excel文件
            killinfo_output_excel_path = KillinfoParser.get_killinfo_output_excel_path(dir)
            grouped.to_excel(killinfo_output_excel_path, index=False)
        else:
            log.warning("Not found any killing data.")

        return killinfo_output_excel_path

    @staticmethod
    def parse_process_die_info(dir):
        process_die_info_output_excel_path = None
        data_list = []
        #08-20 05:02:45.216  1759  8211 I am_proc_died: [0,3968,com.motorola.coresettingsext,920,19]
        pattern = r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{3}\s+\d+\s+\d+\s+I\s+am_proc_died:\s+\[\d+\,(\d+)\,([^,]+)\,(\d+)\,(\d+)\]"
        for root, dirs, files in os.walk(dir):
            for file in files:
                if 'Stream-e' in file or 'logcat' in file:
                    file_path = os.path.join(root, file)
                    log.info(f"Parsing {file_path}")
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        matches = re.findall(pattern, content)
                        for match in matches:
                            data_list.append({
                                'datetime': match[0],
                                'pid': int(match[1]),
                                'pname': match[2],
                                'adj': int(match[3]),
                                'process_state_value': int(match[4]),
                                'process_state_str': KillinfoParser.int_to_process_state(int(match[4])),
                            })
                        
        df = pd.DataFrame(data_list)
        
        if df.empty:
            log.warning("Not found any process die data.")
            return None
        
        log.info(f"df = {df}")
        
        # 确保 datetime 列是日期类型
        df['datetime'] = pd.to_datetime(df['datetime'], format='%m-%d %H:%M:%S')

        # 计算每个 pname 组内的时间差
        df['kill_interval'] = df.groupby('pname')['datetime'].transform(lambda x: x.diff().dt.total_seconds())  # 时间差以秒为单位
        df.to_excel(os.path.join(dir, 'process_die_info_org.xlsx'), index=False)
        
        # 按pname分组并统计个数
        grouped = df.groupby(['pname']).size().reset_index(name='count')

        # 按count大小排序
        grouped = grouped.sort_values(by='count', ascending=False)

        # 打印每个进程的统计结果
        for _, row in grouped.iterrows():
            log.info(f"Process: {row['pname']}")
            log.info(f"Count: {row['count']}")
            
        if not grouped.empty:
            # 保存结果到excel文件
            process_die_info_output_excel_path = os.path.join(dir, 'process_die_info.xlsx')
            grouped.to_excel(process_die_info_output_excel_path, index=False)
        else:
            log.warning("Not found any process die data.")

        return process_die_info_output_excel_path

if __name__ == '__main__':
    log_path = "D:/github/ramct/downloads/NZ4C240007"
    killinfo_output_excel_path = KillinfoParser.parse_killinfo(log_path)
    
    if killinfo_output_excel_path:
        Show.draw_initial_report(log_path, 'test')
        Show.draw_killing(log_path, killinfo_output_excel_path)
