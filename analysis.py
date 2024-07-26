import numpy as np
import pandas as pd
import os

class Analysis():
    @staticmethod
    def get_abnormal_excel_path(dir):
        keyword = os.path.basename(dir)
        file_path = os.path.join(dir,f"{keyword}_abnormal.xlsx")
        return file_path
    
    @staticmethod
    def get_abnormal_json_path(dir):
        keyword = os.path.basename(dir)
        file_path = os.path.join(dir,f"{keyword}_abnormal.json")
        return file_path

    @staticmethod
    # coefficient of variation
    def calculate_cov(data_list):
        if data_list.empty:
            raise ValueError("The input list is empty.")
    
        if not all(isinstance(x, (int, float)) for x in data_list):
            raise TypeError("All elements in the input list must be numeric.")

        mean_value = np.mean(data_list)
        if mean_value == 0:
            raise ZeroDivisionError("The mean value is zero, leading to division by zero.")
        
        standard_deviation = np.std(data_list)
        cov = standard_deviation/mean_value
        return cov
    
    @staticmethod
    def detect_abnormal_data(dataframe:pd.DataFrame, ref_cov, ref_diff):
        dataframe = Analysis.clean_data(dataframe)
        abnormal_data_list = []
        columns = list(dataframe.columns)
        for col in columns[1:]:
            df_col = dataframe[col].dropna()
            if df_col.empty:
                continue
            cov = Analysis.calculate_cov(df_col)
            if cov > ref_cov:
                val_min = np.min(df_col)
                val_max = np.max(df_col)
                val_initial = df_col.iloc[0]
                val_end = df_col.iloc[-1]
                val_diff = val_end-val_initial
                if val_diff > ref_diff:
                    data = {}
                    data['process'] = col
                    data['cov'] = cov
                    data['min'] = val_min
                    data['max'] = val_max
                    data['initial'] = val_initial
                    data['end'] = val_end
                    abnormal_data_list.append(data)
        return abnormal_data_list
    
    @staticmethod
    def clean_data(dataframe:pd.DataFrame):
        dataframe = Analysis.drop_non_perceptible_data(dataframe)
        dataframe = Analysis.drop_heavy_labels_data(dataframe)
        return dataframe

    @staticmethod
    def drop_non_perceptible_data(dataframe:pd.DataFrame):
        light_labels_list = ['PerceptibleMedium', 'AServices', 'BServices','Cached','Previous']
        columns = list(dataframe)
        col_index=None
         # Find the first matching column index
        col_index = next((columns.index(col_name) for col_name in light_labels_list 
                          if col_name in columns), None)
        if col_index:
            columns_to_del = columns[col_index:]
            dataframe = dataframe.drop(columns=columns_to_del)
            
        return dataframe

    @staticmethod
    def drop_heavy_labels_data(dataframe:pd.DataFrame):
        columns_to_del = ['Native', 'System','Persistent','PersistentService',
                             'Foreground','Visible','Perceptible']
        try:
            dataframe = dataframe.drop(columns=columns_to_del)
        except KeyError:
            print(f"{columns_to_del} not found")
        return dataframe
        
    @staticmethod
    def analyze(dir, input_excel_path, ref_cov, ref_diff):
        try:
            df = pd.read_excel(input_excel_path)
        except FileNotFoundError:
            print(f"analyze error: could not found: {input_excel_path}")
            return

        abnormal_data_list = Analysis.detect_abnormal_data(df, ref_cov, ref_diff)
        if abnormal_data_list:
            df = pd.DataFrame(abnormal_data_list)
            excel_path = Analysis.get_abnormal_excel_path(dir)
            df.to_excel(excel_path, index=False)
            json_path = Analysis.get_abnormal_json_path(dir)
            df.to_json(json_path, orient='records')
            
if __name__ == '__main__':
    dir=os.getcwd()
    input_excel_path = "D:/github/ramct/NFNAX10114_output.xlsx"
    ref_cov = 0.25
    ref_diff = 80000
    Analysis.analyze(dir, input_excel_path, ref_cov, ref_diff)