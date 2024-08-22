import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from load_data import CleanData

# Fungsi-fungsi pemrosesan data
def resample_daily(data):
    if 'date' in data.columns:
        data['date'] = pd.to_datetime(data['date'])
        data = data.set_index('date')
    
    if not isinstance(data.index, pd.DatetimeIndex):
        st.error("Indeks data bukan tipe DatetimeIndex. Pastikan kolom 'date' ada dan benar.")
        return pd.DataFrame()

    numeric_cols = data.select_dtypes(include=['number']).columns
    non_numeric_cols = data.select_dtypes(exclude=['number']).columns
    
    resampled_data = data[numeric_cols].resample('D').mean()
    for col in non_numeric_cols:
        resampled_data[col] = data[col].resample('D').first()
    
    return resampled_data.dropna()


def process_data_for_stacked_plot(df):
    record_pm = df[df["date"].dt.year == 2017].copy()
    record_pm['year'] = record_pm['date'].dt.year
    median_pm2_5_by_station = record_pm.groupby('station')['PM2.5'].median().reset_index()
    median_pm10_by_station = record_pm.groupby('station')['PM10'].median().reset_index()
    df_stacked = pd.merge(median_pm2_5_by_station, median_pm10_by_station, on='station', suffixes=('_PM2_5', '_PM10'))
    df_melted = pd.melt(df_stacked, id_vars='station', value_vars=['PM2.5', 'PM10'], 
                        var_name='Pollutant', value_name='Value')
    return df_melted


def calculate_aqi(concentration, pollutant):
    if pollutant == 'NO2':
        breakpoints = [(0, 53), (54, 100), (101, 360), (361, 649), (650, 1249), (1250, 2049)]
        categories = ['Good', 'Moderate', 'Unhealthy for Sensitive Groups', 'Unhealthy', 'Very Unhealthy', 'Hazardous']
    elif pollutant == 'PM10':
        breakpoints = [(0, 54), (55, 154), (155, 254), (255, 354), (355, 424), (425, 604)]
        categories = ['Good', 'Moderate', 'Unhealthy for Sensitive Groups', 'Unhealthy', 'Very Unhealthy', 'Hazardous']
    elif pollutant == 'PM2.5':
        breakpoints = [(0, 12.0), (12.1, 35.4), (35.5, 55.4), (55.5, 150.4), (150.5, 250.4), (250.5, 500.4)]
        categories = ['Good', 'Moderate', 'Unhealthy for Sensitive Groups', 'Unhealthy', 'Very Unhealthy', 'Hazardous']
    elif pollutant == 'O3':
        breakpoints = [(0, 54), (55, 70), (71, 85), (86, 105), (106, 200)]
        categories = ['Good', 'Moderate', 'Unhealthy for Sensitive Groups', 'Unhealthy', 'Very Unhealthy']
    else:
        return None, None

    for i, (low, high) in enumerate(breakpoints):
        if low <= concentration <= high:
            aqi = (high - low) / (breakpoints[i][1] - breakpoints[i][0]) * (concentration - low) + low
            category = categories[i]
            return round(aqi), category
    return None, None
def apply_aqi_calculations(df):
    df['AQI_NO2'], df['AQI_NO2_Category'] = zip(*df['NO2'].apply(lambda x: calculate_aqi(x, 'NO2')))
    df['AQI_PM10'], df['AQI_PM10_Category'] = zip(*df['PM10'].apply(lambda x: calculate_aqi(x, 'PM10')))
    df['AQI_PM2.5'], df['AQI_PM2.5_Category'] = zip(*df['PM2.5'].apply(lambda x: calculate_aqi(x, 'PM2.5')))
    df['AQI_O3'], df['AQI_O3_Category'] = zip(*df['O3'].apply(lambda x: calculate_aqi(x, 'O3')))
    df['AQI'] = df[['AQI_NO2', 'AQI_PM10', 'AQI_PM2.5', 'AQI_O3']].max(axis=1)
    return df
# Fungsi-fungsi visualisasi
def plot_data(data, variables, selected_station):
    fig = px.line(data, x=data.index, y=variables, title=f"Data Harian untuk Stasiun: {selected_station}")
    fig.update_layout(xaxis_title="Tanggal", yaxis_title="Nilai", legend_title="Variabel")
    st.plotly_chart(fig)

def create_stacked_plot(df_melted):
    fig, ax = plt.subplots(figsize=(14, 8))
    colors = ['#1f77b4', '#ff7f0e']
    sns.barplot(x='station', y='Value', hue='Pollutant', data=df_melted, ax=ax, palette=colors)
    ax.set_title('Median PM2.5 and PM10 Concentrations by Station', fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel('Station', fontsize=14, fontweight='bold')
    ax.set_ylabel('Median Concentration (µg/m³)', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f', label_type='edge', fontsize=8, padding=2)
    ax.legend(title='Pollutant', title_fontsize='12', fontsize='10', loc='upper right')
    plt.text(0.02, 0.98, 'Data for Year 2017', transform=ax.transAxes, 
             fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    return fig

def create_aqi_plot(df_merge):
    median_aqi_by_station = df_merge.groupby('station')['AQI'].median().sort_values(ascending=False).reset_index()
    fig, ax = plt.subplots(figsize=(14, 8))
    palette = sns.color_palette("RdYlGn_r", n_colors=len(median_aqi_by_station))
    sns.barplot(x='station', y='AQI', data=median_aqi_by_station, palette=palette, ax=ax)
    ax.set_title('Median Air Quality Index (AQI) by Station', fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel('Station', fontsize=14, fontweight='bold')
    ax.set_ylabel('Median AQI', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)
    for i, v in enumerate(median_aqi_by_station['AQI']):
        ax.text(i, v + 0.5, f'{v:.1f}', ha='center', va='bottom', fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    aqi_categories = [
        (0, 50, 'Good', 'green'),
        (51, 100, 'Moderate', 'yellow'),
        (101, 150, 'Unhealthy for Sensitive Groups', 'orange'),
        (151, 200, 'Unhealthy', 'red'),
        (201, 300, 'Very Unhealthy', 'purple'),
        (301, 500, 'Hazardous', 'maroon')
    ]
    for low, high, label, color in aqi_categories:
        plt.axhline(y=high, color=color, linestyle='--', alpha=0.5)
        plt.text(ax.get_xlim()[1], high, f' {label} ', verticalalignment='bottom', 
                 horizontalalignment='right', color=color, fontweight='bold', fontsize=8)
    plt.text(0.02, 0.98, 'Based on EPA AQI Scale', transform=ax.transAxes, 
             fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    plt.tight_layout()
    return fig

# Fungsi-fungsi perhitungan
def calculate_percentage_change(current, previous):
    return 0 if previous == 0 else ((current - previous) / previous) * 100

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
        return 100
    
    indices = [calculate_index(val, limits[key]) for key, val in zip(['NO2', 'PM10', 'PM2.5', 'O3'], [no2, pm10, pm2_5, o3])]
    caqi = max(indices)
    
    categories = [
        (25, "Sangat Baik"),
        (50, "Baik"),
        (75, "Sedang"),
        (100, "Buruk"),
        (float('inf'), "Sangat Buruk")
    ]
    
    category = next(cat for limit, cat in categories if caqi <= limit)
    
    return round(caqi, 2), category

# Fungsi utama Streamlit
def visual_record_feature():
    st.title("Visualisasi Data Fitur Harian dan CAQI berdasarkan Stasiun")
    
    @st.cache_resource
    def get_clean_data():
        cleaner = CleanData()
        return cleaner.clean()
    
    data = get_clean_data()
    if data is None:
        st.error("Tidak dapat memuat data.")
        return
    
    # Terapkan fungsi apply_aqi_calculations
    data = apply_aqi_calculations(data)
    
    available_features = [f for f in ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3", "TEMP", "PRES", "DEWP", "RAIN", "WSPM"] if f in data.columns]
    
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
        default=['PM10', 'PM2.5'] if all(param in available_features for param in ['NO2', 'PM10', 'PM2.5', 'O3']) else [available_features[0]]
    )

    if not variables:
        st.write("Silakan pilih setidaknya satu variabel.")
        return

    filtered_data = data[data['station'] == selected_station]
    
    if filtered_data.empty:
        st.warning(f"Tidak ada data untuk stasiun: {selected_station}")
        return
    
    daily_data = resample_daily(filtered_data)
    
    # Display CAQI widget
    required_params = ['NO2', 'PM10', 'PM2.5', 'O3']
    if all(param in daily_data.columns for param in required_params):
        last_values = daily_data[required_params].iloc[-1]
        caqi, category = calculate_caqi(*last_values)
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Common Air Quality Index (CAQI)", value=f"{caqi:.2f}", delta=category, delta_color="off")
        with col2:
            suhu_terakhir = daily_data['TEMP'].tail(1).values[0]
            st.metric(label="Suhu terakhir", value=f"{suhu_terakhir:.2f}")
    else:
        st.warning("Data tidak lengkap untuk menghitung CAQI.")
    
    plot_data(daily_data[variables], variables, selected_station)
    
    if st.checkbox('Tampilkan data mentah'):
        st.write(daily_data[variables])
    
    st.subheader("Analisis PM2.5 dan PM10 (2017)")
    df_melted = process_data_for_stacked_plot(data)
    fig_stacked = create_stacked_plot(df_melted)
    st.pyplot(fig_stacked)
    
    st.subheader("Analisis AQI berdasarkan Stasiun")
    fig_aqi = create_aqi_plot(data)
    st.pyplot(fig_aqi)

if __name__ == "__main__":
    visual_record_feature()