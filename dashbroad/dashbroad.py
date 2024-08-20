import streamlit as st
from load_data import CleanData
st.title("Dashbroad")
data_clean = CleanData().clean()
st.dataframe(data_clean)
