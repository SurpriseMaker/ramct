import os
import re
import time
import subprocess
import pandas as pd
from show import Show
from log_utils import log

class LaunchInfoParser():
    @staticmethod
    def get_launch_info_excel_path(dir):
        keyword = os.path.basename(dir)
        file_path = os.path.join(dir, f"{keyword}_launch_info.xlsx")
        return file_path
        
    @staticmethod
    def parse_launchinfo(dir, parse_date=True):
        output_excel_path = None
        data_list = []
        
        #08-03 11:53:46.077  1784  2473 I LaunchCheckinHandler: MotoDisplayed com.google.android.dialer/com.android.dialer.incall.activity.ui.InCallActivity,wp,ca,261
        pattern = r"(\d{2}-\d{2}) \d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+I\s+LaunchCheckinHandler: MotoDisplayed [^,]+\,(\w+)\,(\w+)\,(\d+)"
        for root, dirs, files in os.walk(dir):
            for file in files:
                if 'Stream-s' in file or 'log_' in file:
                    file_path = os.path.join(root, file)
                    #log.info(f"Parsing {file_path}")
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        matches = re.findall(pattern, content)
                        for match in matches:
                            data_list.append({
                                'date': match[0] if parse_date else '01-01',
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

    @staticmethod
    def parse_process_start_info(dir):
        print(f"开始解析进程启动信息,路径: {dir}")
        process_start_info_output_excel_path = None
        data_list = []
        #12-02 23:34:29.964  2751  2933 I am_proc_start: [0,4092,10421,com.dolby.daxservice,added application,com.dolby.daxservice]
        #01-11 12:03:05.281  2387  2482 I am_proc_start: [0,17034,10412,com.motorola.personalize,service,{com.motorola.personalize/com.motorola.personalize.plugin.LockScreenPluginService}]
        pattern = r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{3}\s+\d*+I\s+am_proc_start:\s+\[\d+\,(\d+)\,\d+\,([^,]+)\,([^,]+)\,([^,]+)\]"
        for root, dirs, files in os.walk(dir):
            for file in files:
                if 'Stream-e' in file or 'logcat' in file or 'log_' in file or '-events' in file or 'bugreport-' in file:
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
                                'type': match[3],
                                'component': match[4],
                            })
                        
        df = pd.DataFrame(data_list)
        
        if df.empty:
            log.warning("Not found any process start data.")
            return None
        
        log.info(f"df = {df}")
        
        # 确保 datetime 列是日期类型
        df['datetime'] = pd.to_datetime(df['datetime'], format='%m-%d %H:%M:%S')

        # 计算每个 pname 组内的时间差
        df['start_interval'] = df.groupby('pname')['datetime'].transform(lambda x: x.diff().dt.total_seconds())  # 时间差以秒为单位
        df.to_excel(os.path.join(dir, 'process_start_info_org.xlsx'), index=False)
        
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
            process_start_info_output_excel_path = os.path.join(dir, 'process_start_info.xlsx')
            grouped.to_excel(process_start_info_output_excel_path, index=False)
        else:
            log.warning("Not found any process die data.")

        return process_start_info_output_excel_path

if __name__ == '__main__':
    log_path = r"D:\github\download\glory\IKSWV-76358\NZ4R2C0014_326292077_App_Not_Responding"
    # output_df = pd.DataFrame()

    # # 遍历第一层文件目录
    # if os.path.exists(log_path):
    #     for item in os.listdir(log_path):
    #         item_path = os.path.join(log_path, item)
    #         if os.path.isdir(item_path):
    #             print(f"目录: {item}")
    #             output_sub_path = LaunchInfoParser.parse_launchinfo(item_path, parse_date=False)
    #             sub_df = pd.read_excel(output_sub_path)
    #             output_df = pd.concat([output_df, sub_df], ignore_index=True)
    #         elif os.path.isfile(item_path):
    #             print(f"文件: {item}")
    # else:
    #     print("指定的路径不存在。")

    # output_excel_path = os.path.join(log_path, 'launchinfo_output.xlsx')
    # output_df.to_excel(output_excel_path, index=False)
    
    LaunchInfoParser.parse_process_start_info(log_path)