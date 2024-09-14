import pandas as pd
import matplotlib.pyplot as plt
import os
import mpld3
import argparse
import html

class Comparison:
    def __init__(self, excel_list):
        self.excel_list = excel_list
    
    def gen_html_content(self, h1: str):
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
        return output

    def compare(self):
        df_dict = {}
        for excel_path in self.excel_list:
            df = pd.read_excel(excel_path)
            dir_name = os.path.basename(os.path.dirname(excel_path))
            df_dict[dir_name] = df
        
        # 获取所有 df_dict 的列名
        all_columns = set()
        for dir_name, df in df_dict.items():
            all_columns.update(df.columns)
            
        # 过滤掉非数值的列
        numeric_columns = set()
        for column in all_columns:
            if pd.api.types.is_numeric_dtype(df_dict[next(iter(df_dict))][column]):
                numeric_columns.add(column)
        all_columns = numeric_columns
        
        # 计算子图的行数和列数
        num_plots = len(all_columns)
        rows = (num_plots + 1) // 2
        cols = 2
        
        # 创建子图
        fig, axs = plt.subplots(rows, cols, figsize=(12, 6 * rows))

        markers = 'o'
        # 对每一列进行比较并绘制曲线图
        for index,column in enumerate(all_columns):
            row = index // 2
            coloum = (index) %2
            if rows > 1:
                ax = axs[row][coloum]
            else:
                ax = axs[coloum]
            ax.set_title(column)

            for dir_name, df in df_dict.items():
                if column in df.columns:
                    ax.plot(df[column], label=f'{dir_name}', marker=markers)
            
            # 显示图例
            ax.legend()

        for ax in axs.flatten():
            ax.tick_params(axis='x', labelrotation=30)
        
        plt.tight_layout()
        
        h1 = f"Comparison of {self.excel_list}"
        html_content = self.gen_html_content(h1)
        dir = os.getcwd()
        html_path = os.path.join(dir, 'Comparison_Report.html')
        with open(html_path, 'w') as file:
            file.write(html_content)
            mpld3.save_html(fig, file)
        
        
if __name__ == "__main__":
    #excel_files = ['D:/github/ramct/downloads/paros/U4UQ34.50-3/N1PR160214/N1PR160214_launch_info.xlsx', 'D:/github/ramct/downloads/paros/N1PR160188/N1PR160188_launch_info.xlsx']
    parser = argparse.ArgumentParser(description='Compare Excel files.')
    parser.add_argument('-p', '--paths', nargs='+', help='List of Excel file paths', required=True)
    args = parser.parse_args()
    
    comparison = Comparison(args.paths)
    comparison.compare()