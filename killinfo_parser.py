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
    def parse_kill_categories(dir, parse_date=True):
        killinfo_output_excel_path = None
        data_list = []
        #01-18 17:13:33.654   723   723 I killinfo: [23908,10448,915,201,173576,14,93812,638636,34000,1436,53000,4288,2664712,478784,584484,540460,211764,374244,84116,332916,88448,119632,0,0,840,1016,104,11,0,29268,254540,5,10,2.730000,1.010000,3.010000,0.650000,11.110000]

        #pattern = r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{3}\s+\d+\s+\d+\s+I\s+killinfo:\s+\[\d+\,\d+\,(\d+)\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,(\d+\.\d+)\,(\d+\.\d+)\,(\d+\.\d+)\,(\d+\.\d+)\,(\d+\.\d+)\]"
        pattern_killinfo = re.compile(r"(\d{2}-\d{2}) \d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+I\s+killinfo:\s+\[\d+\,\d+\,(\d+)\,.*")
        #11-26 10:08:09.369  1705  3060 I am_kill : [0,23332,com.google.android.apps.photos,200,crash]
        pattern_amkill = re.compile(r"(\d{2}-\d{2}) \d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+I\s+am_kill\s+:\s+\[\d+\,\d+\,[^,]+\,(\d+)\,.*]")
        for root, dirs, files in os.walk(dir):
            for file in files:
                if 'Stream-e' in file or 'log_' in file:
                    file_path = os.path.join(root, file)
                    #log.info(f"Parsing {file_path}")
                    for line in KillinfoParser.read_lines(file_path):
                        match = pattern_killinfo.search(line)
                        if match:
                            data_list.append({
                                'date': match.group(1) if parse_date else '01-01',
                                'killed_adj': int(match.group(2)),
                            })
                        match2 = pattern_amkill.search(line)
                        if match2:
                            data_list.append({
                                'date': match2.group(1) if parse_date else '01-01',
                                'killed_adj': -1, # -1表示am_kill
                            })
        
        df = pd.DataFrame(data_list)
        
        if df.empty:
            log.warning("Not found any killing data.")
            return None
        
        log.info(f"df = {df}")

        # 使用pd.cut将killed_adj列分箱
        bins = [-float('inf'), 0, 201, 921, float('inf')]
        labels = ['am_kill', 'heavy_kill', 'critical_kill', 'medium_kill']
        df['killed_adj_bin'] = pd.cut(df['killed_adj'], bins=bins, labels=labels, right=False)
        
        # 按日期和分箱结果分组并统计个数
        grouped = df.groupby(['date', 'killed_adj_bin']).size().unstack(fill_value=0)
        
        # 计算每个日期的总数并添加到结果中
        grouped['total_kills'] = grouped.sum(axis=1)
        # 重命名列
        grouped.columns = ['am_kill','heavy_kill', 'critical_kill', 'medium_kill', 'total_kills']
        
        # 将索引转换为列
        grouped.reset_index(inplace=True)
        
        # 将日期字符串转换为日期类型
        grouped['date'] = pd.to_datetime(grouped['date'], format='%m-%d')
        
        # 增加一列 heavy_kill_per_hour
        grouped['heavy_kill_per_hour'] = grouped['heavy_kill'] / 24
        
        dir_name = os.path.basename(dir)
        grouped['dir_name'] = dir_name
        
        # 移动 heavy_kill_per_hour 列到 date 列之后
        grouped = grouped[['date', 'dir_name', 'heavy_kill_per_hour', 'heavy_kill', 'critical_kill','medium_kill', 'am_kill', 'total_kills']]

        # 打印每个日期的统计结果
        for _, row in grouped.iterrows():
            log.info(f"Date: {row['date']}")
            log.info(f"Counts: {row[['heavy_kill', 'critical_kill', 'medium_kill', 'am_kill', 'total_kills']].to_dict()}")
            
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
                if 'Stream-e' in file or 'logcat' in file or 'log_' in file:
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

    @staticmethod
    def parse_top_app_info(dir):
        data_list = []
        #11-04 06:52:31.091  2961  6067 D AppOptManager: onTopAppStateChanged pkg=com.google.android.gms, top= true
        pattern = re.compile(r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{3}\s+\d+\s+\d+\s+D\s+AppOptManager:\s+onTopAppStateChanged\s+pkg=(\S+),\s+top=\s+(\S+)")
        for root, dirs, files in os.walk(dir):
            for file in files:
                if '-system' in file or 'Stream-s' in file or 'log_' in file:
                    file_path = os.path.join(root, file)
                    log.info(f"Parsing {file_path}")
                    for line in KillinfoParser.read_lines(file_path):
                        match = pattern.search(line)
                        if match:
                            data_list.append({
                                'datetime': match.group(1),
                                'pkg': match.group(2),
                                'top': match.group(3),
                            })
                            
        df = pd.DataFrame(data_list)
        
        if df.empty:
            log.warning("Not found any top app data.")
            return None
        
        # 确保 datetime 列是日期类型
        df['datetime'] = pd.to_datetime(df['datetime'], format='%m-%d %H:%M:%S')
    
        log.info(f"df = {df}")
        return df

    @staticmethod
    def parse_killinfo(dir):
        data_list = []
        #01-18 17:13:33.654   723   723 I killinfo: [23908,10448,915,201,173576,14,93812,638636,34000,1436,53000,4288,2664712,478784,584484,540460,211764,374244,84116,332916,88448,119632,0,0,840,1016,104,11,0,29268,254540,5,10,2.730000,1.010000,3.010000,0.650000,11.110000]
        pattern_killinfo = re.compile(r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{3}\s+\d+\s+\d+\s+I\s+killinfo:\s+\[\d+\,\d+\,(\d+)\,.*")
        for root, dirs, files in os.walk(dir):
            for file in files:
                if '-events' in file or 'Stream-e' in file or 'log_' in file:
                    file_path = os.path.join(root, file)
                    #log.info(f"Parsing {file_path}")
                    for line in KillinfoParser.read_lines(file_path):
                        match = pattern_killinfo.search(line)
                        if match:
                            data_list.append({
                                'datetime': match.group(1),
                                'killed_adj': int(match.group(2)),
                            })

        
        df = pd.DataFrame(data_list)
        
        if df.empty:
            log.warning("Not found any killing data.")
            return None
        
        # 确保 datetime 列是日期类型
        df['datetime'] = pd.to_datetime(df['datetime'], format='%m-%d %H:%M:%S')
        
        log.info(f"df = {df}")
        return df
    
    @staticmethod
    def seek_top_apps_in_heavy_kills(dir):
        df_top_apps = KillinfoParser.parse_top_app_info(dir)
        # 去掉 top 列为 False 的行
        df_top_apps = df_top_apps[df_top_apps['top'] != 'false']
        df_top_apps.to_excel(os.path.join(dir, 'top_apps.xlsx'), index=False)
        df_killing = KillinfoParser.parse_killinfo(dir)
        df_killing.to_excel(os.path.join(dir, 'killing_org.xlsx'), index=False)
        # 去掉 df_killing 中 adj 大于 200 的行
        df_killing = df_killing[df_killing['killed_adj'] <= 200]
        df_killing.to_excel(os.path.join(dir, 'killing_le200.xlsx'), index=False)
        # 按 datetime 列合并 df_top_apps 和 df_killing
        merged_df = pd.merge(df_top_apps, df_killing, on='datetime', how='outer')
        
        # 按 datetime 列对合并后的数据进行排序
        merged_df = merged_df.sort_values(by='datetime')
        
        # 对 pkg 和 top 列进行前向填充
        merged_df['pkg'].fillna(method='ffill', inplace=True)
        merged_df['top'].fillna(method='ffill', inplace=True)
        
        # 去掉 killed_adj 列为空的行
        merged_df = merged_df.dropna(subset=['killed_adj'])
        if not merged_df.empty:
            # 保存结果到excel文件
            merged_df_excel_path = os.path.join(dir, 'merged_df.xlsx')
            merged_df.to_excel(merged_df_excel_path, index=False)
            
            # 按 pkg 列统计每种字符串的个数
            pkg_counts = merged_df['pkg'].value_counts()
            
            # 将统计结果转换为 DataFrame
            pkg_counts_df = pkg_counts.reset_index()
            pkg_counts_df.columns = ['pkg', 'count']
            
            # 保存统计结果到excel文件
            pkg_counts_excel_path = os.path.join(dir, 'pkg_counts.xlsx')
            pkg_counts_df.to_excel(pkg_counts_excel_path, index=False)
        else:
            log.warning("Not found any valuable data.")
        
    @staticmethod
    def parse_killinfo_A54(dir):
        data_list = []
        #12-18 14:53:40.936   458   458 I killinfo: [24979,10048,925,201,42392,3,5557988,140228,531180,509984,16688,784,20328,10212,409600,0,323752,85848,4194300,4,1866252,1797292,58816,98640,141188,140692,335728,44112,88460,30620,129140,0,924,396,12,29,0,36796,128832,7,7,17.830000,11.990000,8.250000,1.260000,47.490002,86]
        pattern_killinfo = re.compile(r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{3}\s+\d+\s+\d+\s+I\s+killinfo:\s+\[\d+\,\d+\,(\d+)\,(\d+)\,(\d+)\,(\d+)\,(\d+)\,(\d+)\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,(\d+)\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,\d+\,(\b\d+\.\d+\b),(\b\d+\.\d+\b),(\b\d+\.\d+\b),(\b\d+\.\d+\b),(\b\d+\.\d+\b),\d+\]")
        for root, dirs, files in os.walk(dir):
            for file in files:
                if '-events' in file or 'Stream-e' in file or 'log_' in file:
                    file_path = os.path.join(root, file)
                    #log.info(f"Parsing {file_path}")
                    for line in KillinfoParser.read_lines(file_path):
                        match = pattern_killinfo.search(line)
                        if match:
                            data_list.append({
                                'datetime': match.group(1),
                                'killed_adj': int(match.group(2)),
                                'min_adj': int(match.group(3)),
                                'rss': int(match.group(4)),
                                'reason': int(match.group(5)),
                                'total': int(match.group(6)),
                                'free': int(match.group(7)),
                                'swapfree': int(match.group(8)),
                                'mempsi_some': float(match.group(9)),
                                'mempsi_full': float(match.group(10)),
                                'iopsi_some': float(match.group(11)),
                                'iopsi_full': float(match.group(12)),
                                'cpupsi': float(match.group(13)),
                            })

        
        df = pd.DataFrame(data_list)
        
        if df.empty:
            log.warning("Not found any killing data.")
            return None
        
        # 确保 datetime 列是日期类型
        df['datetime'] = pd.to_datetime(df['datetime'], format='%m-%d %H:%M:%S')
        
        log.info(f"df = {df}")
        return df
    
    @staticmethod
    def analyze_killinfo_A54(dir):
        log_path = r"D:\tools\android\MotoPerfBench\minifps\testData\A54\fill_ram"
        df = KillinfoParser.parse_killinfo_A54(log_path)
        df.to_excel(os.path.join(log_path, 'killinfo_A54.xlsx'), index=False)
        # 按min_adj分组并统计个数
        grouped_min_adj = df.groupby(['min_adj']).size().reset_index(name='count')

        # 按count大小排序
        grouped_min_adj = grouped_min_adj.sort_values(by='count', ascending=False)
        grouped_min_adj.to_excel(os.path.join(log_path, 'grouped_min_adj.xlsx'), index=False)

        # 按reason分组并统计个数
        grouped_reason = df.groupby(['reason']).size().reset_index(name='count')

        # 按count大小排序
        grouped_reason = grouped_reason.sort_values(by='count', ascending=False)
        grouped_reason.to_excel(os.path.join(log_path, 'grouped_reason.xlsx'), index=False)

if __name__ == '__main__':
    log_path = r"D:\tools\android\MotoPerfBench\minifps\testData\fogos\21app\log_interval"
    output_df = pd.DataFrame()

    # 遍历第一层文件目录
    if os.path.exists(log_path):
        for item in os.listdir(log_path):
            item_path = os.path.join(log_path, item)
            if os.path.isdir(item_path):
                print(f"目录: {item}")
                killinfo_output_sub_path = KillinfoParser.parse_kill_categories(item_path, parse_date=False)
                sub_df = pd.read_excel(killinfo_output_sub_path)
                output_df = pd.concat([output_df, sub_df], ignore_index=True)
                KillinfoParser.parse_process_die_info(item_path)
            elif os.path.isfile(item_path):
                print(f"文件: {item}")
    else:
        print("指定的路径不存在。")

    killinfo_output_excel_path = os.path.join(log_path, 'killinfo_output.xlsx')
    output_df.to_excel(killinfo_output_excel_path, index=False)
    if killinfo_output_excel_path:
        Show.draw_initial_report(log_path, 'test')
        Show.draw_killing(log_path, killinfo_output_excel_path, colomn_index_as_x_labels=1)
        
    # log_path = r"D:\github\mlat\mla\download\milos\IKSWV-66545"
    # KillinfoParser.seek_top_apps_in_heavy_kills(log_path)

    