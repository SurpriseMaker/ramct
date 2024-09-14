import subprocess
import time
import matplotlib.pyplot as plt
from datetime import datetime

class CpuMonitor:
    def __init__(self, process_name, device_id=None):
        super().__init__()
        self.process_name = process_name
        self.device_id = device_id
        self.pid = self.get_pid_from_name(process_name)
        self.total_cpu_values = []
        
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
    
    def get_cpu(self):
        if not self.pid:
            print("PID is not available")
            return None
        
        if self.device_id:
            cmd = f"adb -s {self.device_id} shell top -n1 -p {self.pid}"
        else:
            cmd = f"adb shell top -n1 -p {self.pid}"
        
        # 使用 subprocess 模块执行命令
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # 检查命令是否成功执行
        if result.returncode != 0:
            print(f"Error executing command: {result.stderr}")
            return None
        
        # 读取命令的输出
        lines = result.stdout.strip().split('\n')
        
        for line in lines:
            if self.process_name in line:
                parts = line.split()
                if len(parts) > 8:
                    try:
                        cpu_usage = float(parts[8])
                        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(f"cpu usage={cpu_usage} at {current_time}")
                        self.total_cpu_values.append((current_time, cpu_usage))
                        return cpu_usage
                    except ValueError:
                        print(f"Error: parts[8] ('{parts[8]}') cannot be converted to float")
                        return None
        
        print("CPU value not found in the output")
        return None
    
    def monitor_and_plot(self):
        try:
            while True:
                self.get_cpu()
                time.sleep(1)
        except KeyboardInterrupt:
            print("Monitoring stopped by user")
        
        if self.total_cpu_values:
            times, values = zip(*self.total_cpu_values)
            plt.plot(times, values, label=self.process_name)
            plt.xlabel('Time')
            plt.ylabel('CPU usage (%)')
            plt.title('CPU usage over time')
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
    monitor = CpuMonitor("lmkd")
    monitor.monitor_and_plot()