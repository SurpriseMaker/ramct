import matplotlib.pyplot as plt
import mpld3
import os
import html
import pandas as pd
import numpy as np
from log_utils import log

MAX_ITEMS_EACH_CATEGORY = 8
class Show():
    @staticmethod 
    def get_html_path(dir):
        return os.path.join(dir, 'RamUT_Report.html')
    
    @staticmethod
    def gen_html_title(title):
        
        # 生成HTML标题
        template = """
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>RamUT Report</title>
        </head>
        <body>
            <h1 style="text-align: center; color: blue;">{}</h1>
        </body>
        </html>
        """
        
        # Sanitize the input to prevent HTML injection
        sanitized_title = html.escape(title)
        try:
            output = template.format(sanitized_title)
        except Exception as e:
            # Handle any potential exceptions during string formatting
            output = template.format("Error: Invalid input")
            log.info(f"Error generating HTML content: {e}")
        return output
        
    @staticmethod 
    def gen_html_content(h1: str):
        # 将HTML代码嵌入到HTML模板中
        template = """
        <html>
        <head>
        <title>RamUT Report</title>
        </head>
        <body>
        <h1>{}</h1>
        <div></div>
        </body>
        </html>
        """
        # Sanitize the input to prevent HTML injection
        sanitized_h1 = html.escape(h1)
        try:
            output = template.format(sanitized_h1)
        except Exception as e:
            # Handle any potential exceptions during string formatting
            output = template.format("Error: Invalid input")
            log.info(f"Error generating HTML content: {e}")
        return output

    @staticmethod 
    def get_color(index):
        all_colors = ['blue', 'green',  'c', 'k', 'r', 'm', 'pink',
                      'lime','tomato', 'brown', 'chocolate',
                      'gold', 'greenyellow']
        len_all_colors = len(all_colors)
        
        # Ensure index is non-negative
        if index < 0:
            raise ValueError("Index must be non-negative")
  
        index = index % len_all_colors
        return all_colors[index]
    
    @staticmethod 
    def draw_ram_trend(dir, excel_path):
        
        markers = 'o'
        
        try:
            df = pd.read_excel(excel_path)
        except FileNotFoundError:
            log.info(f"draw_ram_trend error: could not found: {excel_path}")
            return

        df_column_list = df.columns.to_list()
        log.info(f"df={df}")
        fig, axs = plt.subplots(4, 2, figsize=(12, 25))
        
        ax = axs[0][0]
        ax.set_title("Overview, KBs by oom_adj category")
        y_labels_list = ['Native', 'System','Persistent','PersistentService','Foreground','Visible',	'Perceptible']
        x_labels = 'file_name'
        for index, y_labels in enumerate(y_labels_list):
            ax.plot(df[x_labels], df[y_labels], label=y_labels, marker=markers, color=Show.get_color(index))
        ax.legend()
        
        y_labels_list.append('PerceptibleMedium')
        for index1, label in enumerate(y_labels_list):
            if index1 >= len(y_labels_list) -1:
                break
            if label not in df_column_list:
                continue
            start = df_column_list.index(label) + 1
            end = df_column_list.index(y_labels_list[index1 + 1]) if index1 < len(y_labels_list) - 1 else len(df_column_list)
            end = min(end, start + MAX_ITEMS_EACH_CATEGORY)

            row = int((index1 + 1) /2)
            column = (index1 +1) %2
            if row >= 4 or column >= 2:
                log.info(f"Skipping plot for label {label} due to subplot index out of bounds")
                continue
            log.info(f"label={label}, start={start}, end = {end}, row = {row}, column = {column}")
            ax = axs[row][column]
            title = f"{label}, KBs by process"
            ax.set_title(title)
            for index2 in range(start, end):
                y_labels = df_column_list[index2]
                ax.plot(df[x_labels], df[y_labels], label=y_labels, marker=markers, color=Show.get_color(index2))
            ax.legend()
        
        for ax in axs.flatten():
            ax.tick_params(axis='x', labelrotation=30)

        plt.tight_layout()

        h1 = "Ram Usage Trend"
        html_content = Show.gen_html_content(h1)

        # Ensure dir is defined and valid
        if dir is None or not os.path.isdir(dir):
            log.error("Invalid directory path")
            raise ValueError("Invalid directory path")

        html_path = Show.get_html_path(dir)
        # 将HTML网页保存到文件
        try:
            with open(html_path, 'a') as file:
                file.write(html_content)
                mpld3.save_html(fig, file)
        except Exception as e:
            log.error(f"Error writing to file: {e}")

    @staticmethod 
    def draw_killing(dir, excel_path):
        markers = 'o'

        df = pd.read_excel(excel_path)
        df_column_list = df.columns.to_list()
        fig, axs = plt.subplots(int(len(df_column_list)/3), 3, figsize=(12, 4 * int(len(df_column_list)/3)))
        
        x_labels = df_column_list[0]
        for index, y_labels in enumerate(df_column_list[1:]):
            row = int(index /3)
            coloum = (index) %3
            ax = axs[row][coloum]
            ax.set_title(y_labels)
            ax.plot(df[x_labels], df[y_labels], label=y_labels, marker=markers, color=Show.get_color(index))
            
        for ax in axs.flatten():
            ax.tick_params(axis='x', labelrotation=30)
            
        plt.tight_layout()
        
        h1 = "Kill Information"
        html_content = Show.gen_html_content(h1)
        html_path = Show.get_html_path(dir)
        with open(html_path, 'a') as file:
            file.write(html_content)
            mpld3.save_html(fig, file)
    
    @staticmethod 
    def draw_launch_info(dir, excel_path):
        markers = 'o'

        df = pd.read_excel(excel_path)
        df_column_list = df.columns.to_list()
        
        # 计算子图的行数和列数, df的第一列是时间戳
        num_plots = len(df_column_list) -1
        rows = (num_plots + 3) // 3
        cols = 3

        fig, axs = plt.subplots(rows, cols, figsize=(12, 4 * rows))
        
        x_labels = df_column_list[0]
        for index, y_labels in enumerate(df_column_list[1:]):
            row = int(index /3)
            coloum = (index) %3
            ax = axs[row][coloum]
            ax.set_title(y_labels)
            ax.plot(df[x_labels], df[y_labels], label=y_labels, marker=markers, color=Show.get_color(index))
            
        for ax in axs.flatten():
            ax.tick_params(axis='x', labelrotation=30)
            
        plt.tight_layout()
        
        h1 = "App Launch Information"
        html_content = Show.gen_html_content(h1)
        html_path = Show.get_html_path(dir)
        with open(html_path, 'a') as file:
            file.write(html_content)
            mpld3.save_html(fig, file)
            
            
    @staticmethod
    def draw_abnormal_processes(dir, df, df_abnormal):
        markers = 'o'
        abnormal_name_list = df_abnormal['process'].to_list()

        # 确保 df 至少有一列
        if df.shape[1] > 0:
            x_labels = df.columns.to_list()[0]
        else:
            raise ValueError("DataFrame has no columns")

        # 计算子图的行数和列数
        num_plots = len(abnormal_name_list)
        rows = (num_plots + 1) // 2
        cols = 2

        log.info(f"draw_abnormal_processes, num_plots={num_plots}, rows={rows}, cols={cols}")
        
        # 创建子图
        fig, axs = plt.subplots(rows, cols, figsize=(12, 6 * rows))

        for index, name in enumerate(abnormal_name_list):
            if name not in df.columns:
                continue
            row = int(index /2)
            coloum = (index) %2
            if rows > 1:
                ax = axs[row][coloum]
            else:
                ax = axs[coloum]
            ax.set_title(name)
            ax.plot(df[x_labels], df[name], label=name, marker=markers, color=Show.get_color(index))
            
        for ax in axs.flatten():
            ax.tick_params(axis='x', labelrotation=30)
            
        plt.tight_layout()
        
        h1 = "Possible Abnormal Processes"
        html_content = Show.gen_html_content(h1)
        html_path = Show.get_html_path(dir)
        html_str = df_abnormal.to_html(index=False)
        with open(html_path, 'a') as file:
            file.write(html_content)
            file.write(html_str)
            mpld3.save_html(fig, file)
            
    @staticmethod
    def draw_initial_report(dir, title):
        html_title = Show.gen_html_title(title)
        html_path = Show.get_html_path(dir)
        with open(html_path, 'w') as file:
            file.write(html_title)
            
    @staticmethod
    def draw_pss_report(dir, excel_path):
        MIN_PSS_TO_DRAW = 40000 # 绘图的最小PSS值，小于此值的进程将不绘图，单位KB
        df = pd.read_excel(excel_path)
        
        # 获取DataFrame的索引
        df_index = df.index
        
        # 去掉列元素最大值小于MIN_PSS_TO_DRAW的列
        df = df.loc[:, df.max() >= MIN_PSS_TO_DRAW]

        # 按列中元素的最大值排序
        sorted_columns = df.max().sort_values(ascending=False).index
        df = df[sorted_columns]

        df_column_list = df.columns.to_list()

        # 计算子图的行数和列数
        num_plots = len(df_column_list)
        cols = 2
        rows = num_plots// MAX_ITEMS_EACH_CATEGORY // cols + 1 if num_plots % MAX_ITEMS_EACH_CATEGORY != 0 else num_plots// MAX_ITEMS_EACH_CATEGORY // cols

        log.info(f"draw_pss_report, num_plots={num_plots}, rows={rows}, cols={cols}")
        
        # 创建子图
        fig, axs = plt.subplots(rows, cols, figsize=(12, 6 * rows))
        
        # 遍历每一列并绘图
        for index, column in enumerate(df_column_list):
            ax_row = int(index/MAX_ITEMS_EACH_CATEGORY /2)
            ax_coloum = int(index/MAX_ITEMS_EACH_CATEGORY) %2
            if rows > 1:
                ax = axs[ax_row][ax_coloum]
            else:
                ax = axs[ax_coloum]
            ax.set_title("PSS by Process in KBs")
            ax.plot(df_index, df[column], label=column, marker='o', color=Show.get_color(index))
            ax.legend()
        ax.tick_params(axis='x', labelrotation=30)
        plt.tight_layout()
        
        h1 = f"PSS by Process, peak {MIN_PSS_TO_DRAW} KBs or above "
        html_content = Show.gen_html_content(h1)
        html_path = Show.get_html_path(dir)
        with open(html_path, 'a') as file:
            file.write(html_content)
            mpld3.save_html(fig, file)