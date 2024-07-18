import numpy as np
import pandas as pd
import os

class Analysis():
    @staticmethod
    def get_abnormal_excel_path(dir):
        keyword = os.path.basename(dir)
        file_path = os.path.join(dir,
                                       f"{keyword}_abnormal.xlsx")
        return file_path
    
    @staticmethod
    # coefficient of variation
    def caculate_cov(data_list):
        mean_value = np.mean(data_list)
        
        standard_deviation = np.std(data_list)
        
        cov = standard_deviation/mean_value
        return cov
    
    @staticmethod
    def detect_abnormal_data(dataframe:pd.DataFrame, ref_cov, ref_diff):
        dataframe = Analysis.clean_data(dataframe)
        exception_data_list = []
        columns = list(dataframe)
        for col in columns[1:]:
            df_col = dataframe[col].dropna()
            cov = Analysis.caculate_cov(df_col)
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
                    exception_data_list.append(data)
        return exception_data_list
    
    def clean_data(dataframe:pd.DataFrame):
        dataframe = Analysis.drop_non_perceptible_data(dataframe)
        dataframe = Analysis.drop_heavy_labels_data(dataframe)
        return dataframe
            
    def drop_non_perceptible_data(dataframe:pd.DataFrame):
        light_labels_list = ['PerceptibleMedium', 'AServices', 'BServices','Cached','Previous']
        columns = list(dataframe)
        col_index=None
        for label in light_labels_list:
            for col_name in columns:
                if label == col_name:
                    col_index=columns.index(col_name)
                    print(f"col_index={col_index}")
                    break
            if col_index:
                break
        if col_index:
            columns_to_del = columns[col_index:]
            dataframe = dataframe.drop(columns=columns_to_del)
            
        return dataframe
    
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

        exception_data_list = Analysis.detect_abnormal_data(df, ref_cov, ref_diff)
        if exception_data_list:
            df = pd.DataFrame(exception_data_list)
            excel_path = Analysis.get_abnormal_excel_path(dir)
            df.to_excel(excel_path, index=False)
            
if __name__ == '__main__':
    dir=os.getcwd()
    input_excel_path = "D:/github/ramct/NFNAX10114_output.xlsx"
    ref_cov = 0.25
    ref_diff = 80000
    Analysis.analyze(dir, input_excel_path, ref_cov, ref_diff)