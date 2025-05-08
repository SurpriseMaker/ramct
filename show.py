import matplotlib.pyplot as plt
import mpld3
import os
import html
import pandas as pd
import numpy as np
from log_utils import log
from version_parser import VersionParser
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math

KBYTES_PER_MB = 1024
MAX_ITEMS_EACH_CATEGORY = 8
class Show():
    @staticmethod 
    def get_html_path(dir):
        return os.path.join(dir, 'RamUT_Report.html')
    
    @staticmethod
    def gen_html_title(title):
        # 生成HTML标题（支持多行）
        template = """
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>RamUT Report</title>
            <style>
                .title-line {{
                    display: block;
                    margin: 5px 0;
                }}
            </style>
        </head>
        <body>
            <h1 style="text-align: center; color: blue;">
                {0}
            </h1>
        </body>
        </html>
        """
        
        # 处理多行标题
        try:
            # 分割标题为多行并转义HTML
            lines = [html.escape(line.strip()) for line in title.split('\n') if line.strip()]
            formatted_lines = '<br>'.join(lines)
            
            output = template.format(formatted_lines)
        except Exception as e:
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
                      'lime','tomato', 'brown',
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
        ax.set_title("Overview, MBs by oom_adj category")
        y_labels_list = ['Native', 'System','Persistent','PersistentService','Foreground','Visible','Perceptible']
        x_labels = df_column_list[0]
        for index, y_labels in enumerate(y_labels_list):
            ax.plot(df[x_labels], df[y_labels]//KBYTES_PER_MB, label=y_labels, marker=markers, color=Show.get_color(index))
        ax.legend()
        
        for end_tag in ['PerceptibleMedium', 'PerceptibleLow', 'AServices', 'Previous', 'BServices', 'Cached']:
            if end_tag in df_column_list:
                y_labels_list.append(end_tag)
                break

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
            title = f"{label}, MBs by process"
            ax.set_title(title)
            for index2 in range(start, end):
                y_labels = df_column_list[index2]
                ax.plot(df[x_labels], df[y_labels]//KBYTES_PER_MB, label=y_labels, marker=markers, color=Show.get_color(index2))
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
                log.info(f"draw_ram_trend, saved to {html_path}")
        except Exception as e:
            log.error(f"Error writing to file: {e}")
            
        Show.draw_ram_status_trend(dir, excel_path)

    @staticmethod 
    def draw_ram_status_trend(dir, excel_path):
        markers = 'o'
        
        try:
            df = pd.read_excel(excel_path)
        except FileNotFoundError:
            log.info(f"draw_ram_status_trend error: could not found: {excel_path}")
            return

        df_column_list = df.columns.to_list()
        log.info(f"df={df}")
        fig, ax = plt.subplots(1, 1, figsize=(6, 6))

        ax.set_title("Ram Status Trend, MBs")
        x_labels = df_column_list[0]
        start = df_column_list.index('Free RAM')
        end = df_column_list.index('ZRAM')
        for index in range(start, end):
            y_labels = df_column_list[index]
            ax.plot(df[x_labels], df[y_labels]//KBYTES_PER_MB, label=y_labels, marker=markers, color=Show.get_color(index))
        ax.legend()

        ax.tick_params(axis='x', labelrotation=30)

        plt.tight_layout()

        h1 = "Ram Status Trend"
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
                log.info(f"draw_ram_status_trend, saved to {html_path}")
        except Exception as e:
            log.error(f"Error writing to file: {e}")

    @staticmethod 
    def draw_killing(dir, excel_path, colomn_index_as_x_labels=0):
        markers = 'o'

        df = pd.read_excel(excel_path)
        df_column_list = df.columns.to_list()
        
        # 计算子图的行数和列数, df的第一列是时间戳
        num_plots = len(df_column_list) - 2
        cols = 2
        rows = num_plots // cols + 1 if num_plots % cols != 0 else num_plots // cols

        fig, axs = plt.subplots(rows, cols, figsize=(12, 4 * rows))

        x_labels = df_column_list[colomn_index_as_x_labels]
        for index, y_labels in enumerate(df_column_list[2:]):
            row = index // cols
            coloum = index % cols
            if rows > 1:
                ax = axs[row][coloum]
            else:
                ax = axs[coloum]
            ax.set_title(y_labels)
            if colomn_index_as_x_labels == 1:
                ax.set_xticks(range(len(df[x_labels])))  # 设置固定的刻度位置
                ax.set_xticklabels(df[x_labels], rotation=30)  # 设置 x 轴标签为字符串并旋转
            ax.plot(df[x_labels], df[y_labels], label=y_labels, marker=markers, color=Show.get_color(index))
            
        # for ax in axs.flatten():
        #     ax.tick_params(axis='x', labelrotation=30)
            
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
        num_plots = len(df_column_list) - 1
        cols = 3
        rows = num_plots // cols + 1 if num_plots % cols != 0 else num_plots // cols

        fig, axs = plt.subplots(rows, cols, figsize=(12, 4 * rows))
        
        x_labels = df_column_list[0]
        for index, y_labels in enumerate(df_column_list[1:]):
            row = index // 3
            coloum = (index) %3
            if rows > 1:
                ax = axs[row][coloum]
            else:
                ax = axs[coloum]
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
            row = index // 2
            coloum = (index) %2
            if rows > 1:
                ax = axs[row][coloum]
            else:
                ax = axs[coloum]
            title = f"{name}, MBs"
            ax.set_title(title)
            ax.plot(df[x_labels], df[name]//KBYTES_PER_MB, label=name, marker=markers, color=Show.get_color(index))
            
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
        MIN_PSS_TO_DRAW = 200000  # KB

        df = pd.read_excel(excel_path)
        df = df[df['pss'] >= MIN_PSS_TO_DRAW]  # 前置过滤

        # 1. 动态计算最佳布局
        packages = df.groupby('package')['pss'].max().sort_values(ascending=False).index
        n_plots = len(packages)
        rows = math.ceil(n_plots / 2)  # 每行2图

        # 2. 创建响应式画布
        fig = make_subplots(
            rows=rows, cols=2,
            subplot_titles=[f"<b>{pkg}</b>" for pkg in packages],
            shared_yaxes=True
        )

        # 3. 高性能批量绘图
        for i, pkg in enumerate(packages):
            pkg_data = df[df['package'] == pkg]
            row = (i // 2) + 1
            col = (i % 2) + 1

            fig.add_trace(
                go.Scatter(
                    x=pkg_data['datetime'],
                    y=pkg_data['pss']/1024,  # 直接转换为MB
                    name=pkg,
                    mode='lines+markers',
                    marker_symbol=i % 30,
                    line_shape='spline',
                    hovertemplate="<b>%{y:.1f} MB</b><br>%{x|%H:%M}</b><extra></extra>"
                ),
                row=row, col=col
            )

        # 4. 智能交互配置
        fig.update_layout(
            # 精确高度控制
            height=100 + (300 * rows),  # 标题区100px + 内容区300px/行

            # 紧凑标题设置
            title={
                'text': f"PSS Report (>{MIN_PSS_TO_DRAW//1024} MB)",
                'y': 1.0,  # 顶部
                'yanchor': 'top',
                'font': {'size': 24},
                'pad': {'t': 5, 'b': 5}  # 标题内边距（上下各5px）
            },

            # 边距精细控制（单位：px）
            margin=dict(
                t=80,    # 增加顶部边距（原30+50）
                b=20,
                l=60,
                r=40,
                pad=50   # 新增：图表区域整体下移50px
            ),
            updatemenus=[{
                "buttons": [
                    {"method": "relayout", "label": "Linear", "args": [{"yaxis.type": "linear"}]},
                    {"method": "relayout", "label": "Log", "args": [{"yaxis.type": "log"}]}
                ],
                "type": "dropdown",
                "x": 0.5,
                "y": 0.99  # 贴近顶部
            }]
        )


        # 5. 输出优化

        html_path = os.path.join(dir, "pss_report.html")
        fig.write_html(
            html_path,
            full_html=True,
            include_plotlyjs='cdn',
            animation_opts={'frame': {'redraw': False}}
        )
        
        html_path = Show.get_html_path(dir)
        with open(html_path, 'a') as f:  # 追加模式
            f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))

            
    @staticmethod
    def draw_cpu_report(dir, excel_path):
        PROCESSES_PER_PAGE = 2  # 每页显示的进程数
        MIN_CPU_TO_DRAW = 0.5  # 绘图的最小CPU值，小于此值的进程将不绘图，单位百分比
        df = pd.read_excel(excel_path)

        datetime_df = df.iloc[:, 0]  # 使用 iloc 选取第一列作为时间戳
        category_df = df.iloc[:, 1:5]  # 使用 iloc 选取第2-5列作为分类数据
        processes_df = df.iloc[:, 5:]  # 使用 iloc 选取后面的所有列

        processes_df = processes_df.loc[:, processes_df.fillna(0).mean() >= MIN_CPU_TO_DRAW]

        sorted_columns = processes_df.fillna(0).mean().sort_values(ascending=False).index
        processes_df = processes_df[sorted_columns]
        # 合并分类数据和进程数据
        df_to_draw = pd.concat([category_df, processes_df], axis=1)

        column_list_to_draw = df_to_draw.columns.to_list()

        # 计算子图的行数和列数
        num_plots = len(column_list_to_draw)
        pages = (num_plots // PROCESSES_PER_PAGE) + (1 if num_plots % PROCESSES_PER_PAGE > 0 else 0)

        log.info(f"draw_cpu_report, num_plots={num_plots}, pages={pages}")

        # 创建HTML内容
        html_content = f"<h1>CPU Usages, mean {MIN_CPU_TO_DRAW}% or above</h1>"

        # 添加分页按钮
        html_content += "<div class='pagination'>"
        for page_num in range(pages):
            html_content += f"<button onclick='showPage({page_num + 1})'>Page {page_num + 1}</button>"
        html_content += "</div>"

        # 为每一页创建一个 div
        for page_num in range(pages):
            html_content += f"<div class='page' id='page-{page_num + 1}' style='display: {'none' if page_num > 0 else 'block'};'>"

            # 创建子图
            fig, axs = plt.subplots(PROCESSES_PER_PAGE, 1, figsize=(12, 2 * PROCESSES_PER_PAGE), squeeze=False)
            for index in range(PROCESSES_PER_PAGE):
                global_index = page_num * PROCESSES_PER_PAGE + index
                if global_index < num_plots:
                    column = column_list_to_draw[global_index]
                    ax = axs[index, 0]
                    ax.set_title(f"{column} (%)")
                    ax.plot(datetime_df, df_to_draw[column], label=column, marker='o', color=Show.get_color(global_index))
                    ax.legend()

            plt.tight_layout()

            # 保存图表为HTML片段
            html_snippet = mpld3.fig_to_html(fig)
            html_content += html_snippet  # 将图表的HTML片段直接添加
            plt.close(fig)  # 关闭该图形以释放内存
            html_content += "</div>"

        # 添加分页按钮
        html_content += "<div class='pagination'>"
        for page_num in range(pages):
            html_content += f"<button onclick='showPage({page_num + 1})'>Page {page_num + 1}</button>"
        html_content += "</div>"

        # 添加JavaScript进行分页
        javascript = """
        <script>
        function showPage(pageNum) {
            var pages = document.getElementsByClassName('page');
            for (var i = 0; i < pages.length; i++) {
                pages[i].style.display = 'none';
            }
            document.getElementById('page-' + pageNum).style.display = 'block'; 
        }
        </script>
        """

        html_content += javascript

        html_path = Show.get_html_path(dir)
        with open(html_path, 'a') as file:
            file.write(html_content)
