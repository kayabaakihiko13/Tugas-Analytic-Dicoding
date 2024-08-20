import streamlit as st
from load_data import CleanData
from visualization import visual_record_feature
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
