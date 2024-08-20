import streamlit as st
from load_data import CleanData
import pandas as pd
import plotly.express as px

def resample_daily(data):
    # Pastikan kolom 'date' ada dan dijadikan sebagai indeks
    if 'date' in data.columns:
        data['date'] = pd.to_datetime(data['date'])  # Konversi ke datetime jika belum
        data = data.set_index('date')  # Set kolom 'date' sebagai indeks
    
    # Validasi apakah index sudah berupa DatetimeIndex
    if not isinstance(data.index, pd.DatetimeIndex):
        st.error("Indeks data bukan tipe DatetimeIndex. Pastikan kolom 'date' ada dan benar.")
        return pd.DataFrame()  # Mengembalikan DataFrame kosong jika indeks tidak valid

    numeric_cols = data.select_dtypes(include=['number']).columns
    non_numeric_cols = data.select_dtypes(exclude=['number']).columns
    
    resampled_data = data[numeric_cols].resample('D').mean()  # Resample dengan rata-rata harian
    for col in non_numeric_cols:
        resampled_data[col] = data[col].resample('D').first()  # Ambil nilai pertama dari setiap hari
    
    return resampled_data.dropna()

def plot_data(data, variables, selected_station):
    fig = px.line(data, x=data.index, y=variables, title=f"Data Harian untuk Stasiun: {selected_station}")
    fig.update_layout(
        xaxis_title="Tanggal",
        yaxis_title="Nilai",
        legend_title="Variabel"
    )
    st.plotly_chart(fig)

def calculate_percentage_change(current, previous):
    if previous == 0:
        return 0  # Avoid division by zero
    return ((current - previous) / previous) * 100

def calculate_caqi(no2, pm10, pm2_5, o3):
    limits = {
        'NO2': [0, 50, 100, 200, 400],
        'PM10': [0, 25, 50, 90, 180],
        'PM2.5': [0, 15, 30, 55, 110],
        'O3': [0, 60, 120, 180, 240]
    }
    
    def calculate_index(value, limits):
        for i, limit in enumerate(limits[1:], 1):
            if value <= limit:
                lower_limit = limits[i-1]
                return (i - 1) * 25 + ((value - lower_limit) / (limit - lower_limit)) * 25
        return 100  # Jika melebihi batas tertinggi
    
    indices = [
        calculate_index(no2, limits['NO2']),
        calculate_index(pm10, limits['PM10']),
        calculate_index(pm2_5, limits['PM2.5']),
        calculate_index(o3, limits['O3'])
    ]
    
    caqi = max(indices)
    
    if caqi <= 25:
        category = "Sangat Baik"
    elif caqi <= 50:
        category = "Baik"
    elif caqi <= 75:
        category = "Sedang"
    elif caqi <= 100:
        category = "Buruk"
    else:
        category = "Sangat Buruk"
    
    return round(caqi, 2), category

def display_caqi_widget(data):
    required_params = ['NO2', 'PM10', 'PM2.5', 'O3']
    if not all(param in data.columns for param in required_params):
        st.warning("Data tidak lengkap untuk menghitung CAQI.")
        return

    last_values = data[required_params].iloc[-1]
    caqi, category = calculate_caqi(*last_values)

    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="Common Air Quality Index (CAQI)",
            value=f"{caqi:.2f}",
            delta=category,
            delta_color="off"
        )
    
    with col2:
        suhu_terakhir = data['TEMP'].tail(1).values[0]
        st.metric(label="Suhu terakhir", value=f"{suhu_terakhir:.2f}")
def visual_record_feature():
    @st.cache_resource
    def get_clean_data():
        cleaner = CleanData()
        return cleaner.clean()
    
    def get_available_features(data):
        features = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3", "TEMP", "PRES", "DEWP", "RAIN", "WSPM"]
        return [f for f in features if f in data.columns]
    
    st.title("Visualisasi Data Fitur Harian dan CAQI berdasarkan Stasiun")
    
    data = get_clean_data()
    if data is None:
        return
    
    available_features = get_available_features(data)
    if not available_features:
        st.error("Tidak ada fitur yang tersedia dalam data.")
        return
    
    if 'station' not in data.columns:
        st.error("Kolom 'station' tidak ditemukan dalam data.")
        return
    
    stations = sorted(data['station'].unique())
    selected_station = st.selectbox('Pilih stasiun', stations)
    
    variables = st.multiselect(
        'Pilih variabel untuk ditampilkan',
        available_features,
        default=['PM10', 'PM2.5'] if all(param in available_features for param in ['NO2', 'PM10', 'PM2.5', 'O3'])
        else [available_features[0]]
    )

    if not variables:
        st.write("Silakan pilih setidaknya satu variabel.")
        return

    filtered_data = data[data['station'] == selected_station]
    
    if filtered_data.empty:
        st.warning(f"Tidak ada data untuk stasiun: {selected_station}")
        return
    
    daily_data = resample_daily(filtered_data)
    
    display_caqi_widget(daily_data)
    
    plot_data(daily_data[variables], variables, selected_station)
    
    if st.checkbox('Tampilkan data mentah'):
        st.write(daily_data[variables])
