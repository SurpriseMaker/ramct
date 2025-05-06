import getopt
import os, sys
import traceback
import gzip
import time
import zipfile

from mi_parser import ParseMeminfo
from show import Show
from analysis import Analysis
from killinfo_parser import KillinfoParser
from launchinfo_parser import LaunchInfoParser
from pss_parser import PssParser
from cpu_parser import CpuParser
from log_utils import log
from version import __version__

SPLIT_LINE = "################################"

def unzip_all_gz_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.gz'):
                gz_file_path = os.path.join(root, file)
                output_file_path = os.path.join(root, file[:-3])  # Remove the '.gz' extension
                
                with gzip.open(gz_file_path, 'rb') as f_in:
                    with open(output_file_path, 'wb') as f_out:
                        f_out.write(f_in.read())
                
                print(f"unziped: {gz_file_path} -> {output_file_path}")
                # 删除原文件
                os.remove(gz_file_path)
                
            if file.endswith('.zip'):
                zip_file_path = os.path.join(root, file)
                
                try:
                    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                        zip_ref.extractall(root)

                    print(f"解压: {zip_file_path} -> {root}")
                    # 删除原文件
                    os.remove(zip_file_path)
                except zipfile.BadZipFile:
                    print(f"错误: 文件 {zip_file_path} 不是一个有效的 ZIP 文件或已经损坏。")
                except Exception as e:
                    print(f"解压文件时发生错误 {zip_file_path}: {e}")


def read_version_file(dir_path):
    """
    遍历指定目录查找version.txt文件并读取其内容
    
    参数:
        dir_path (str): 要搜索的目录路径
        
    返回:
        str: version.txt文件的内容，如果找不到文件则返回None
    """
    version_content = None
    
    # 遍历目录
    for root, dirs, files in os.walk(dir_path):
        if 'version.txt' in files:
            version_path = os.path.join(root, 'version.txt')
            try:
                with open(version_path, 'r', encoding='utf-8') as f:
                    version_content = f.read().strip()
                break  # 找到文件后停止搜索
            except IOError as e:
                print(f"无法读取version.txt文件: {e}")
                return None
    
    return version_content

def analyze_data(parser, analysis_func, show_func, data_type):
    log.info(SPLIT_LINE)
    log.info(f"Beginning of {data_type} Analysis....")
    log.info(SPLIT_LINE)
    start_second = time.time()
    try:
        excel_path = parser(dir)
        if excel_path:
            analysis_func(dir, excel_path, ref_cov, ref_diff)
            show_func(dir, excel_path)
        else:
            log.warning(f"NOT FOUND ANY {data_type.upper()} INFO DATA!!!")
    except Exception as e:
        log.error(f"Error during {data_type} analysis: {e}")
        log.error(traceback.format_exc())
    
    end_second = time.time()
    log.info(f"End of {data_type} Analysis. duration: {end_second - start_second} seconds.")

if __name__ == '__main__':
    argv = sys.argv[1:]
    dir=os.getcwd()
    ref_cov = 0.25
    ref_diff = 80000
 
    log.info(f"RamUT version:{__version__}")
    try:
        opts, args = getopt.getopt(argv, "p:c:d:")  # 短选项模式
    except getopt.GetoptError:
        log.info("Error in get option")
        sys.exit(1)

    log.info(f"--opts={opts}\n--arg={args}")
    for opt, opt_value in opts:
        if opt in ['-p']:
            dir = opt_value
        if opt in ['-c']:
            try:
                ref_cov = float(opt_value)
            except ValueError:
                log.info("Error: -c option requires a float value")
                sys.exit(1)
        if opt in ['-d']:
            try:
                ref_diff = int(opt_value)
            except ValueError:
                log.info("Error: -d option requires an integer value")
                sys.exit(1)

    unzip_all_gz_files(dir)
    sw_version = read_version_file(dir)
    report_titile = (f"RamUT Report for {dir}\n"
                   f"build version:{sw_version}\n"
                   f"tool version:{__version__}")

    Show.draw_initial_report(dir, report_titile)

    # Ram Consumption Analysis
    analyze_data(ParseMeminfo.parse_all_files, Analysis.analyze, Show.draw_ram_trend, "Ram Usage")
    
    # Kill infos Analysis
    analyze_data(KillinfoParser.parse_kill_categories, lambda *args: None, Show.draw_killing, "Kill infos")
    #analyze_data(KillinfoParser.parse_process_die_info, lambda *args: None, Show.draw_killing, "Die infos")
    
    # Launch infos Analysis
    analyze_data(LaunchInfoParser.parse_launchinfo, lambda *args: None, Show.draw_launch_info, "Launch infos")
    
    # CPU Analysis
    analyze_data(CpuParser.parse_cpu_data, lambda *args: None, Show.draw_cpu_report, "CPU Usage")

    # Pss of process Analysis
    analyze_data(PssParser.parse_pss_data, lambda *args: None, Show.draw_pss_report, "Pss of process")
    log.info("Finished.")