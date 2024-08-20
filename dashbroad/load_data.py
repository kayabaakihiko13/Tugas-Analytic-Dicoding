import pandas as pd
import requests
import numpy as np
import warnings
from numba import jit
from scipy import stats

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

    @staticmethod
    @jit(nopython=True)
    def _fill_nan_numba(data, nan_mask):
        filled_data = data.copy()
        non_nan_data = data[~nan_mask]
        
        if len(non_nan_data) > 1:
            mean = np.mean(non_nan_data)
            std = np.std(non_nan_data)
            t_stat = (mean - np.mean(non_nan_data)) / (std / np.sqrt(len(non_nan_data)))
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), len(non_nan_data) - 1))
            
            fill_value = mean if p_value < 0.005 else np.median(non_nan_data)
        else:
            fill_value = np.median(non_nan_data) if len(non_nan_data) > 0 else 0
        
        filled_data[nan_mask] = fill_value
        return filled_data

    def fill_nan(self):
        variables = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3", "TEMP", "PRES", "DEWP", "RAIN", "WSPM"]
        
        for station in self.df["station"].unique():
            station_mask = self.df['station'] == station
            for variable in variables:
                data = self.df.loc[station_mask, variable].values
                nan_mask = np.isnan(data)
                self.df.loc[station_mask, variable] = self._fill_nan_numba(data, nan_mask)
        
        return self.df

    def format_date(self):
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
        self.fill_nan()
        self.format_date()
        return self.df