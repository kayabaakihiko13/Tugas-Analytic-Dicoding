import pandas as pd
import streamlit as st
from load_data import CleanData
from visualization import visual_record_feature
@st.cache_resource
def load_data():
        BASE_URL = "../PRSA_Data_20130301-20170228/"
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
@st.cache_resource
def get_clean_data():
    cleaner = CleanData()
    return cleaner.clean()

st.title("Dashboard")

cleaned_data = get_clean_data()

if cleaned_data is not None:
    visual_record_feature()
else:
    st.error("Data tidak dapat dimuat.")
