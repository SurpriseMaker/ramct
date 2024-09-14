import subprocess
import time
import matplotlib.pyplot as plt
from datetime import datetime

class PssMonitor:
    def __init__(self, process_name, device_id=None):
        super().__init__()
        self.process_name = process_name
        self.device_id = device_id
        self.pid = self.get_pid_from_name(process_name)
        self.total_pss_values = []
        
    def get_pid_from_name(self, process_name):
        if self.device_id:
            cmd = f"adb -s {self.device_id} shell ps -e | grep {process_name}"
        else:
            cmd = f"adb shell ps -e | grep {process_name}"
        
        # 使用 subprocess 模块执行命令
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # 检查命令是否成功执行
        if result.returncode != 0:
            print(f"Error executing command: {result.stderr}")
            return None
        
        # 读取命令的输出
        lines = result.stdout.strip().split('\n')
        
        if not lines:
            print(f"No output from command: {cmd}")
            return None
        
        # 解析第一行的第二列
        parts = lines[0].split()
        if len(parts) < 2:
            print(f"Unexpected output format: {lines[0]}")
            return None
        
        pid = parts[1]
        print(f"Process ID={pid}")
        return pid

    def get_total_pss(self):
        if not self.pid:
            print("PID is not available")
            return None
        
        if self.device_id:
            cmd = f"adb -s {self.device_id} shell dumpsys meminfo {self.pid}"
        else:
            cmd = f"adb shell dumpsys meminfo {self.pid}"
        
        # 使用 subprocess 模块执行命令
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # 检查命令是否成功执行
        if result.returncode != 0:
            print(f"Error executing command: {result.stderr}")
            return None
        
        # 读取命令的输出
        lines = result.stdout.strip().split('\n')
        
        for line in lines:
            if "TOTAL PSS:" in line:
                parts = line.split()
                if len(parts) > 1:
                    total_pss = int(parts[2])
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"Total PSS={total_pss} at {current_time}")
                    self.total_pss_values.append((current_time, total_pss))
                    return total_pss
        
        print("TOTAL PSS not found in the output")
        return None

    def monitor_and_plot(self):
        try:
            while True:
                self.get_total_pss()
                time.sleep(3)
        except KeyboardInterrupt:
            print("Monitoring stopped by user")
        
        if self.total_pss_values:
            times, values = zip(*self.total_pss_values)
            plt.plot(times, values, label=self.process_name)
            plt.xlabel('Time')
            plt.ylabel('Total PSS')
            plt.title('Total PSS over time')
            # 选择性地显示 x 轴标签
            num_labels = 10  # 显示的标签数量
            if len(times) > num_labels:
                step = len(times) // num_labels
                plt.xticks(range(0, len(times), step), times[::step], rotation=45)
            else:
                plt.xticks(rotation=45)
            plt.legend()
            plt.tight_layout()
            plt.show()
        else:
            print("No data to plot")

if __name__ == "__main__":
    monitor = PssMonitor("com.motorola.launcher3")
    monitor.monitor_and_plot()