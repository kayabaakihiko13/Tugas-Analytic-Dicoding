import pandas as pd
import requests
from io import StringIO
import warnings
from scipy import stats
import numpy as np

warnings.filterwarnings("ignore")

class CleanData:
    def __init__(self):
        self.df = self.__load_data()

    def __load_data(self):
        BASE_URL = "https://raw.githubusercontent.com/kayabaakihiko13/Tugas-Analytic-Dicoding/main/PRSA_Data_20130301-20170228/"
        stations = [
            "Aotizhongxin", "Changping", "Dingling", "Dongsi", "Guanyuan",
            "Gucheng", "Huairou", "Nongzhanguan", "Shunyi", "Tiantan",
            "Wanliu", "Wanshouxigong"
        ]

        dataframes = []

        for station in stations:
            url = f"{BASE_URL}PRSA_Data_{station}_20130301-20170228.csv"
            try:
                df = pd.read_csv(url)
                dataframes.append(df)
            except Exception as e:
                print(f"Failed to retrieve data for {station}: {e}")

        if not dataframes:
            raise ValueError("No CSV files were successfully retrieved")

        return pd.concat(dataframes, ignore_index=True)

    def __fill_nan(self):
        variables = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3", "TEMP", "PRES", "DEWP", "RAIN", "WSPM"]
        
        for station in self.df["station"].unique():
            station_data = self.df[self.df['station'] == station]
            
            for variable in variables:
                non_nan_data = station_data[variable].dropna()
                
                if len(non_nan_data) > 1:
                    _, p_value = stats.ttest_1samp(non_nan_data, station_data[variable].mean())
                    
                    fill_value = station_data[variable].mean() if p_value < 0.005 else station_data[variable].median()
                else:
                    fill_value = station_data[variable].median()
                
                self.df.loc[(self.df['station'] == station) & self.df[variable].isna(), variable] = fill_value
        
        return self.df

    def __format_date(self):
        self.df['date'] = pd.to_datetime(
            self.df['year'].astype(str) + '-' +
            self.df['month'].astype(str).str.zfill(2) + '-' +
            self.df['day'].astype(str).str.zfill(2) + ' ' +
            self.df['hour'].astype(str).str.zfill(2) + ':00:00'
        )
        
        columns = ['date'] + [col for col in self.df.columns if col != 'date']
        self.df = self.df[columns]
        
        return self.df

    def clean(self):
        self.__fill_nan()
        self.__format_date()
        return self.df
