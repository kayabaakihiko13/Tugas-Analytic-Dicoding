import glob
import os
import pandas as pd

def load_data():
    FOLDER_PATH = "../PRSA_Data_20130301-20170228/"
    csv_files = glob.glob(os.path.join(FOLDER_PATH, '*.csv'))

    # Periksa apakah ada file yang ditemukan
    if not csv_files:
        raise FileNotFoundError(f"Tidak ada file CSV yang ditemukan di folder {FOLDER_PATH}")

    # Jika ada file yang ditemukan, gabungkan mereka menjadi satu DataFrame
    df_merge = pd.concat([pd.read_csv(file) for file in csv_files], ignore_index=True)

    return df_merge