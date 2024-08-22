import pandas as pd
import numpy as np
from numba import jit
import requests
import warnings
import math
import streamlit as st
warnings.filterwarnings("ignore")

@jit(nopython=True)
def t_cdf(t, df):
    x = df / (t**2 + df)
    return 1.0 - 0.5 * betainc(0.5*df, 0.5, x)

@jit(nopython=True)
def betainc(a, b, x):
    if x < 0 or x > 1:
        return 0.0
    
    if x == 0 or x == 1:
        return x
    
    lbeta = math.lgamma(a+b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(math.log(x)*a + math.log(1-x)*b - lbeta) / a
    
    f = 1.0
    c = 1.0
    d = 0.0
    
    for i in range(200):
        temp = -(a+i) * (a+b+i) * x / ((a+2*i) * (a+2*i+1))
        d = 1.0 + temp * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + temp / c
        d = 1.0 / d
        f *= d * c
        if abs(d*c - 1.0) < 1e-8:
            return front * (f - 1.0)
    
    return front * (f - 1.0)

class CleanData:
    def __init__(self):
        self.df = self.load_data()

    @staticmethod
    @st.cache_data(show_spinner=False)
    def load_data():
        BASE_URL = "./PRSA_Data_20130301-20170228/"
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
                st.warning(f"Failed to retrieve data for {station}: {e}")

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
            p_value = 2 * (1 - t_cdf(abs(t_stat), len(non_nan_data) - 1))
            
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
        with st.spinner('Cleaning data...'):
            self.fill_nan()
            self.format_date()
        return self.df