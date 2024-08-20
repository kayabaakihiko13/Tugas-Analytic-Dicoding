import streamlit as st
from load_data import CleanData

@st.cache_resource
def get_clean_data():
    cleaner = CleanData()
    return cleaner.clean()
st.title("Dashbroad")
cleaned_data = get_clean_data()
st.dataframe(cleaned_data.head())