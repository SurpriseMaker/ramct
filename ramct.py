import getopt
import os, sys

from mi_parser import ParseMeminfo
from show import Show
from analysis import Analysis
from killinfo_parser import KillinfoParser

VERSION=2.1
if __name__ == '__main__':
    argv = sys.argv[1:]
    dir=os.getcwd()
    ref_cov = 0.25
    ref_diff = 80000
 
    print(f"ramct version:{VERSION}")
    try:
        opts, args = getopt.getopt(argv, "-p:-c:-d:")  # 短选项模式
    except:
        print("Error in get option")

    print(f"--opts={opts}\n--arg={args}")
    for opt, opt_value in opts:
        if opt in ['-p']:
            dir = opt_value
        if opt in ['-c']:
            ref_cov = opt_value
        if opt in ['-d']:
            ref_diff = opt_value

    # Ram Consumption Analysis
    print("##########################################")
    print("##########################################")
    print("Beginning of Ram Consumption Analysis....")
    meminfo_excel_path = ParseMeminfo.parseAllFiles(dir)
    if meminfo_excel_path:
        Analysis.analyze(dir, meminfo_excel_path, ref_cov, ref_diff)
        Show.draw_ram_trend(dir, meminfo_excel_path)
    else:
        print("NOT FOUND ANY MEMORY INFO DATA!!!")
    print("End of Ram Consumption Analysis.")
    print("##########################################")
    print("##########################################")
    
    print("Beginning of Kill infos Analysis....")
    # Kill infos
    killinfo_excel_path = KillinfoParser.parse_killinfo(dir)
    if killinfo_excel_path:
        Show.draw_killing(dir, killinfo_excel_path)
    else:
        print("NOT FOUND ANY KILL INFO DATA!!!")
    print("End of Kill infos Analysis.")