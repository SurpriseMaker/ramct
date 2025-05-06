import re
import os
from typing import Dict, List, Optional, Tuple

class VersionParser:
    """
    用于解析Android bugreport文件中APK版本信息的静态工具类
    所有方法均为类方法，无需实例化即可使用
    """
    
    # 预编译正则表达式，提升性能
    _VERSION_PATTERN = re.compile(
        r'Package\s+\[([^\]]+)\].*?versionName=([^\s\n]+)',
        re.DOTALL
    )
    
    # 默认文件编码
    DEFAULT_ENCODING = 'utf-8'

    @classmethod
    def extract_apk_versions(cls, bugreport_content: str, encoding: str = DEFAULT_ENCODING) -> Dict[str, str]:
        """
        从bugreport内容中提取APK版本信息
        
        参数:
            bugreport_content: bugreport文件内容
            encoding: 文件编码格式（保留参数，实际由调用方处理）
            
        返回:
            字典格式: {packageName: versionName}
        """
        matches = cls._VERSION_PATTERN.findall(bugreport_content)
        return {pkg.strip(): ver.strip() for pkg, ver in matches}
    
    @classmethod
    def _get_file_mtime(cls, file_path: str) -> Tuple[float, str]:
        """
        获取文件修改时间和路径的元组
        
        参数:
            file_path: 文件路径
            
        返回:
            (修改时间, 文件路径) 元组
        """
        return (os.path.getmtime(file_path), file_path)

    @classmethod
    def find_latest_bugreport_file(cls, directory: str) -> Optional[str]:
        """
        查找目录中最后一个（最新的）bugreport文件
        
        参数:
            directory: 要搜索的目录路径
            
        返回:
            最新的bugreport文件完整路径，如果没有找到返回None
        """
        bugreport_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if (file.lower().startswith('bugreport') and 
                    file.lower().endswith('.txt')):
                    file_path = os.path.join(root, file)
                    bugreport_files.append(cls._get_file_mtime(file_path))
        
        # 按修改时间降序排序，取最新的
        if bugreport_files:
            bugreport_files.sort(reverse=True)
            return bugreport_files[0][1]
        return None

    @classmethod
    def parse_apk_versions_from_latest_bugreport(cls, directory: str, encoding: str = DEFAULT_ENCODING) -> Dict[str, str]:
        """
        处理目录中最后一个（最新的）bugreport文件
        
        参数:
            directory: 要处理的目录路径
            encoding: 文件编码格式，默认为utf-8
            
        返回:
            字典格式: {packageName: versionName}
            如果没有找到文件返回空字典
        """
        latest_file = cls.find_latest_bugreport_file(directory)
        if not latest_file:
            print(f"No bugreport files found in {directory}")
            return {}
        
        try:
            with open(latest_file, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()
            return cls.extract_apk_versions(content)
        except Exception as e:
            print(f"Error processing file {latest_file}: {e}")
            return {}

# 使用示例
if __name__ == "__main__":
    # 直接使用类方法，无需实例化
    target_directory = r'D:\github\download\milos\IKSWV-136151'
    versions = VersionParser.parse_apk_versions_from_latest_bugreport(target_directory)
    
    # 打印结果
    print("最新bugreport文件中的APK版本信息:")
    for pkg, ver in versions.items():
        print(f"  {pkg}: {ver}")
