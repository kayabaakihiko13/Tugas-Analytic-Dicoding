import streamlit as st
from load_data import load_data
st.title("Dashbroad")
st.dataframe(load_data().head())
