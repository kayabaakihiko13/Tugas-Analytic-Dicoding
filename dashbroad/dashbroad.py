import streamlit as st
from load_data import CleanData

@st.cache_resource
def get_clean_data():
    cleaner = CleanData()
    return cleaner.clean()

cleaned_data = get_clean_data()
st.dataframe(cleaned_data)