import pandas as pd
import streamlit as st
from io import BytesIO
import requests
import matplotlib.pyplot as plt

# Judul aplikasi
st.title("Aplikasi Visualisasi Data Transaksi")

# ID file Google Drive
file_id = "1p2PYISBdkAdFIFf41chb5ltw39L35ztP"
url = f"https://drive.google.com/uc?export=download&id={file_id}"

# Fungsi untuk membaca data dari Google Drive
@st.cache_data
def load_data():
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = BytesIO(response.content)
            df = pd.read_csv(data, sep=',', encoding='utf-8', on_bad_lines='skip')
            df['tgl_transaksi'] = pd.to_datetime(df['tgl_transaksi'], errors='coerce')
            return df
        else:
            st.error(f"Gagal memuat data. Status code: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error saat memuat data: {e}")
        return None

# Memuat data
df = load_data()

if df is not None:
    # Sidebar untuk navigasi
    menu = st.sidebar.selectbox("Menu", ["Filter Data", "Visualisasi"]) 

    # Menu 1: Filter Data
    if menu == "Filter Data":
        st.header("Filter Data")

        # Radio button untuk memilih kode level
        level_options = ["kd_lv_1", "kd_lv_2", "kd_lv_3", "kd_lv_4", "kd_lv_5", "kd_lv_6"]
        selected_level = st.radio("Pilih Kode Level", level_options)
        account_column = selected_level.replace("kd_", "nm_")

        # Radio button untuk memilih tipe unit
        unit_options = ["nm_unit", "nm_sub_unit"]
        selected_unit_type = st.radio("Pilih Tipe Unit", unit_options)

        # Multiselect untuk unit/sub unit
        unique_units = df[selected_unit_type].dropna().unique().tolist()
        selected_units = st.multiselect(f"Pilih {selected_unit_type}", unique_units)

        # Multiselect untuk nama akun
        unique_accounts = df[account_column].dropna().unique().tolist()
        selected_accounts = st.multiselect(f"Pilih Nama Akun ({account_column})", unique_accounts)

        # Slider rentang bulan
        months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                  "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        month_map = {month: idx+1 for idx, month in enumerate(months)}
        selected_month_range = st.select_slider(
            "Pilih Rentang Bulan",
            options=months,
            value=("Januari", "Desember")
        )

        # Terapkan filter
        filtered_df = df.copy()

        # Filter berdasarkan nama akun
        if selected_accounts:
            filtered_df = filtered_df[filtered_df[account_column].isin(selected_accounts)]

        # Filter berdasarkan unit/sub unit
        if selected_units:
            filtered_df = filtered_df[filtered_df[selected_unit_type].isin(selected_units)]

        # Filter berdasarkan rentang bulan
        start_month = month_map[selected_month_range[0]]
        end_month = month_map[selected_month_range[1]]
        filtered_df = filtered_df[
            (filtered_df['tgl_transaksi'].dt.month >= start_month) &
            (filtered_df['tgl_transaksi'].dt.month <= end_month)
        ]

        # Hitung total debet, kredit, dan saldo
        total_debet = filtered_df['debet'].sum()
        total_kredit = filtered_df['kredit'].sum()
        saldo = total_debet - total_kredit

        # Tambahkan baris total dan saldo
        jumlah_row = {
            "nomor": "", "no_bukti": "", "tgl_transaksi": "",
            selected_unit_type: "", account_column: "Jumlah",
            "debet": total_debet, "kredit": total_kredit, "uraian": ""
        }
        saldo_row = {
            "nomor": "", "no_bukti": "", "tgl_transaksi": "",
            selected_unit_type: "", account_column: "Saldo",
            "debet": saldo if saldo > 0 else 0,
            "kredit": abs(saldo) if saldo < 0 else 0,
            "uraian": ""
        }
        final_df = pd.concat([
            filtered_df,
            pd.DataFrame([jumlah_row]),
            pd.DataFrame([saldo_row])
        ], ignore_index=True)

        # Tampilkan tabel
        st.dataframe(final_df)

        # Download Excel
        @st.cache_data
        def convert_to_excel(df_):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_.to_excel(writer, index=False, sheet_name="Filtered_Data")
            output.seek(0)
            return output.getvalue()

        if not final_df.empty:
            excel_data = convert_to_excel(final_df)
            st.download_button(
                label="Download Data (Excel)",
                data=excel_data,
                file_name="filtered_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Tidak ada data yang sesuai dengan filter.")

    # Menu 2: Visualisasi
    elif menu == "Visualisasi":
        st.header("Visualisasi Data")
        st.warning("Fitur visualisasi sedang dalam pengembangan.")
