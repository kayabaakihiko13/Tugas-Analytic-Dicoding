import pandas as pd
import requests
from io import StringIO

def load_data():
    BASE_URL = "https://raw.githubusercontent.com/kayabaakihiko13/Tugas-Analytic-Dicoding/main/PRSA_Data_20130301-20170228/"
    file_names = [
        "PRSA_Data_Aotizhongxin_20130301-20170228.csv",
        "PRSA_Data_Changping_20130301-20170228.csv",
        "PRSA_Data_Dingling_20130301-20170228.csv",
        "PRSA_Data_Dongsi_20130301-20170228.csv",
        "PRSA_Data_Guanyuan_20130301-20170228.csv",
        "PRSA_Data_Gucheng_20130301-20170228.csv",
        "PRSA_Data_Huairou_20130301-20170228.csv",
        "PRSA_Data_Nongzhanguan_20130301-20170228.csv",
        "PRSA_Data_Shunyi_20130301-20170228.csv",
        "PRSA_Data_Tiantan_20130301-20170228.csv",
        "PRSA_Data_Wanliu_20130301-20170228.csv",
        "PRSA_Data_Wanshouxigong_20130301-20170228.csv"
    ]

    dataframes = []

    for file_name in file_names:
        url = BASE_URL + file_name
        response = requests.get(url)
        
        if response.status_code == 200:
            csv_content = StringIO(response.text)
            df = pd.read_csv(csv_content)
            dataframes.append(df)
        else:
            print(f"Failed to retrieve {file_name}")

    if not dataframes:
        raise ValueError("No CSV files were successfully retrieved")

    df_merge = pd.concat(dataframes, ignore_index=True)

    return df_merge