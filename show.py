import matplotlib.pyplot as plt
import mpld3
import os
import pandas as pd

class Show():
        
    def get_html_path(dir):
        return os.path.join(dir, 'RamConsumption.html')
    
    def gen_html_content(h1: str):
        # 将HTML代码嵌入到HTML模板中
        template = """
        <html>
        <head>
        <title>RAM C.T. Report</title>
        </head>
        <body>
        <h1>{}</h1>
        <div></div>
        </body>
        </html>
        """
        output = template.format(h1)
        return output

    def get_color(index):
        all_colors = ['blue', 'green',  'c', 'k', 'r', 'm', 'pink',
                      'lime','tomato', 'brown', 'chocolate', 'darkred',
                      'gold', 'greenyellow']
        len_all_colors = len(all_colors)
        while index >= len_all_colors:
            index = index - len_all_colors
            
        return all_colors[index]
        
    def draw_ram_trend(dir, excel_path):
        MAX_ITEMS_EACH_CATEGORY = 10
        markers = 'o'
        
        try:
            df = pd.read_excel(excel_path)
        except FileNotFoundError:
            print(f"draw_ram_trend error: could not found: {excel_path}")
            return

        df_column_list = df.columns.to_list()
        print(f"df={df}")
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
            if not (label in df_column_list):
                continue
            start = df_column_list.index(label) + 1
            end = df_column_list.index(y_labels_list[index1+1])
            end = min(end, start + MAX_ITEMS_EACH_CATEGORY)

            row = int((index1 + 1) /2)
            coloum = (index1 +1) %2
            print(f"label={label}, start={start}, end = {end}, row = {row}, column = {coloum}")
            ax = axs[row][coloum]
            title = f"{label}, KBs by process"
            ax.set_title(title)
            for index2 in range(start, end):
                y_labels = df_column_list[index2]
                ax.plot(df[x_labels], df[y_labels], label=y_labels, marker=markers, color=Show.get_color(index2))
            ax.legend()
        
        for ax in axs.flatten():
            ax.tick_params(axis='x', labelrotation=30)

        plt.tight_layout()
        
        # 将图表转换为HTML
        html_code = df.to_html()

        h1 = "RAM Consumption Trend"
        html_content = Show.gen_html_content(h1)

        html_path = Show.get_html_path(dir)
        # 将HTML网页保存到文件
        with open(html_path, 'w') as file:
            file.write(html_content)
            mpld3.save_html(fig, file)

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
            
    def draw_launch_info(dir, excel_path):
        markers = 'o'

        df = pd.read_excel(excel_path)
        df_column_list = df.columns.to_list()
        fig, axs = plt.subplots(int(len(df_column_list)/3)+1, 3, figsize=(12, 4 * int(len(df_column_list)/3)))
        
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