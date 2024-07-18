import getopt
import os, sys

from mi_parser import ParseMeminfo
from show import Show
from analysis import Analysis

VERSION=2.0
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

    output_excel_path = ParseMeminfo.get_output_excel_path(dir)
    ParseMeminfo.parseAllFiles(dir, output_excel_path)
    Analysis.analyze(dir, output_excel_path, ref_cov, ref_diff)
    Show.draw_ram_trend(dir, output_excel_path)