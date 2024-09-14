import pandas as pd

class LMKDParser:
    def parse_lmkd(excel_path, output_path):
        df = pd.read_excel(excel_path)
        
        # 筛选 mempsi 列大于 4 的数据
        df_critical = df.loc[df['mempsi'] > 4]
        
        # 统计 reason 列为 -1 的占比
        reason_minus_one_count = df_critical['reason'].value_counts().get(-1, 0)
        total_critical_count = len(df_critical)
        minus_one_ratio = reason_minus_one_count / total_critical_count if total_critical_count > 0 else 0
        
        
        print(f"critical count: {total_critical_count}, reason -1 count: {reason_minus_one_count}, reason -1 ratio: {minus_one_ratio}")
        
         # 统计 adj_killed 列非空值的比例
        adj_killed_non_null_count = df_critical['adj_killed'].count()
        adj_killed_non_null_ratio = adj_killed_non_null_count / total_critical_count if total_critical_count > 0 else 0
        
        print(f"adj_killed non-null count: {adj_killed_non_null_count}, lmkd effectiveness ratio: {adj_killed_non_null_ratio}")
        
        # 保存结果到文件
        df_critical.to_excel(output_path, index=False)
        
if __name__ == '__main__':
    excel_path = 'D:/glory/polling/100/4/lowmemorykiller.txt_output.xlsx'
    output_path = 'D:/glory/polling/100/4/reason.xlsx'
    LMKDParser.parse_lmkd(excel_path, output_path)