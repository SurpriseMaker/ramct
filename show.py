import matplotlib.pyplot as plt
import mpld3
import os
import pandas as pd

class Show():
        
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
        
        df = pd.read_excel(excel_path)
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
        #plt.Show()
        
        # 将图表转换为HTML
        html_code = df.to_html()
        #mpld3.save_html(fig, 'plot.html')

        # 将HTML代码嵌入到HTML模板中
        template = """
        <html>
        <head>
        <title>RAM Consumption Trend</title>
        </head>
        <body>
        <h1>RAM Consumption Trend</h1>
        <div>{}</div>
        </body>
        </html>
        """

        output = template.format(html_code)

        html_path = os.path.join(dir, 'RamConsumption.html')
        # 将HTML网页保存到文件
        with open(html_path, 'w') as file:
            mpld3.save_html(fig, file)
            file.write(output)

    def draw_killing(dir, excel_path):
        markers = 'o'

        df = pd.read_excel(excel_path)
        df_column_list = df.columns.to_list()
        fig, axs = plt.subplots(2, 2, figsize=(12, 12))
        
        x_labels = df_column_list[0]
        for index, y_labels in enumerate(df_column_list[1:]):
            row = int(index /2)
            coloum = (index) %2
            ax = axs[row][coloum]
            ax.set_title(y_labels)
            ax.plot(df[x_labels], df[y_labels], label=y_labels, marker=markers, color=Show.get_color(index))
            
        for ax in axs.flatten():
            ax.tick_params(axis='x', labelrotation=30)
            
        plt.tight_layout()
        
        html_path = os.path.join(dir, 'KillInfo.html')
        with open(html_path, 'w') as file:
            mpld3.save_html(fig, file)