import getopt
import os, sys
import traceback
import gzip
import time

from mi_parser import ParseMeminfo
from show import Show
from analysis import Analysis
from killinfo_parser import KillinfoParser
from launchinfo_parser import LaunchInfoParser
from pss_parser import PssParser
from log_utils import log
from version import __version__

SPLIT_LINE = "##########################################\n##########################################"

def unzip_all_gz_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.gz'):
                gz_file_path = os.path.join(root, file)
                output_file_path = os.path.join(root, file[:-3])  # Remove the '.gz' extension
                
                with gzip.open(gz_file_path, 'rb') as f_in:
                    with open(output_file_path, 'wb') as f_out:
                        f_out.write(f_in.read())
                
                print(f"解压完成: {gz_file_path} -> {output_file_path}")
                # 删除原文件
                os.remove(gz_file_path)

def analyze_data(parser, analysis_func, show_func, data_type):
    log.info(SPLIT_LINE)
    log.info(f"Beginning of {data_type} Analysis....")
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
    report_titile = f"RamUT Report for {dir}, version:{__version__}"
    Show.draw_initial_report(dir, report_titile)

    # Ram Consumption Analysis
    analyze_data(ParseMeminfo.parse_all_files, Analysis.analyze, Show.draw_ram_trend, "Ram Usage")
    
    # Kill infos Analysis
    analyze_data(KillinfoParser.parse_killinfo, lambda *args: None, Show.draw_killing, "Kill infos")
    
    # Launch infos Analysis
    analyze_data(LaunchInfoParser.parse_launchinfo, lambda *args: None, Show.draw_launch_info, "Launch infos")
    
    # Pss of process Analysis
    analyze_data(PssParser.parse_pss_data, lambda *args: None, Show.draw_pss_report, "Pss of process")
    log.info("Finished.")