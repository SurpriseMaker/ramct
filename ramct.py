import getopt
import os, sys
import logging

from mi_parser import ParseMeminfo
from show import Show
from analysis import Analysis
from killinfo_parser import KillinfoParser
from launchinfo_parser import LaunchInfoParser

VERSION=3.0
SPLIT_LINE = "##########################################\n##########################################"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='ramct.log')

def analyze_data(parser, analysis_func, show_func, data_type):
    logging.info(f"Beginning of {data_type} Analysis....")
    try:
        excel_path = parser(dir)
        if excel_path:
            analysis_func(dir, excel_path, ref_cov, ref_diff)
            show_func(dir, excel_path)
        else:
            logging.warning(f"NOT FOUND ANY {data_type.upper()} INFO DATA!!!")
    except Exception as e:
        logging.error(f"Error during {data_type} analysis: {e}")
    logging.info(f"End of {data_type} Analysis.")

if __name__ == '__main__':
    argv = sys.argv[1:]
    dir=os.getcwd()
    ref_cov = 0.25
    ref_diff = 80000
 
    print(f"ramct version:{VERSION}")
    try:
        opts, args = getopt.getopt(argv, "p:c:d:")  # 短选项模式
    except getopt.GetoptError:
        print("Error in get option")
        sys.exit(1)

    print(f"--opts={opts}\n--arg={args}")
    for opt, opt_value in opts:
        if opt in ['-p']:
            dir = opt_value
        if opt in ['-c']:
            try:
                ref_cov = float(opt_value)
            except ValueError:
                print("Error: -c option requires a float value")
                sys.exit(1)
        if opt in ['-d']:
            try:
                ref_diff = int(opt_value)
            except ValueError:
                print("Error: -d option requires an integer value")
                sys.exit(1)

    # Ram Consumption Analysis
    analyze_data(ParseMeminfo.parse_all_files, Analysis.analyze, Show.draw_ram_trend, "Ram Consumption")
    
    # Kill infos Analysis
    analyze_data(KillinfoParser.parse_killinfo, lambda *args: None, Show.draw_killing, "Kill infos")
    
    # Launch infos Analysis
    analyze_data(LaunchInfoParser.parse_launchinfo, lambda *args: None, Show.draw_launch_info, "Launch infos")
    
    logging.info("Finished.")