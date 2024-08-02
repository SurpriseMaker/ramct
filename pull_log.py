
import requests
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import gzip

def download_file(url, destination):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(destination, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        print(f"文件已下载: {destination}")
    else:
        print(f"下载失败: {url}")

def download_all_files(base_url, destination_folder):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    
    response = requests.get(base_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            file_url = urljoin(base_url, link['href'])
            print(f"正在下载: {file_url}")
            if file_url.endswith('/'):  # 如果是目录，则递归下载
                pass
                # dir_name = file_url.split('/')[-2]
                # if dir_name not in exclude_dirs:
                #     sub_folder = os.path.join(destination_folder, dir_name)
                #     download_all_files(file_url, sub_folder, exclude_dirs)
                # else:
                #     print(f"跳过目录: {file_url}")
            else:  # 如果是文件，则下载
                file_name = file_url.split('/')[-1]
                if 'Stream' in file_name or 'meminfo' in file_name:
                    destination_path = os.path.join(destination_folder, file_name)
                    download_file(file_url, destination_path)
    else:
        print(f"无法访问目录: {base_url}")



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
                print(f"删除原文件: {gz_file_path}")

if __name__ == '__main__':
    DOWNLOAD_FOLDER = "./downloads"
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
        
    url_list = [
        "http://logger.stability.mot.com/dumpsys_meminfo/NFNA2N0280/2024-07-22/",

    ]
    for base_url in url_list:
        device_id = base_url.split('/')[-3]
        date_folder = base_url.split('/')[-2]
        # 目标文件夹
        destination_folder = os.path.join(DOWNLOAD_FOLDER, device_id, date_folder)

        # 下载所有文件
        download_all_files(base_url, destination_folder)

        unzip_all_gz_files(destination_folder)