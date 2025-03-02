import pandas as pd
import streamlit as st
from io import BytesIO
import requests

# Judul aplikasi
st.title("Aplikasi Visualisasi Data Transaksi")

# ID file Google Drive
file_id = "1p2PYISBdkAdFIFf41chb5ltw39L35ztP"
url = f"https://drive.google.com/uc?export=download&id={file_id}"

# Fungsi untuk membaca data dari Google Drive
@st.cache_data
def load_data():
    try:
        # Unduh file dari Google Drive
        response = requests.get(url)
        if response.status_code == 200:
            data = BytesIO(response.content)
            df = pd.read_csv(data, sep=',', encoding='utf-8', on_bad_lines='skip')
            
            # Pastikan kolom tgl_transaksi dalam format datetime
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
    menu = st.sidebar.selectbox("Menu", ["Data Lengkap", "Filter Data"])

    # Menu 1: Data Lengkap
    if menu == "Data Lengkap":
        st.header("Data Lengkap")
        st.dataframe(df)

    # Menu 2: Filter Data
    elif menu == "Filter Data":
        st.header("Filter Data")

        # Radio button untuk memilih kode level
        level_options = ["kd_lv_1", "kd_lv_2", "kd_lv_3", "kd_lv_4", "kd_lv_5", "kd_lv_6"]
        selected_level = st.radio("Pilih Kode Level", level_options)

        # Tentukan nama akun berdasarkan level yang dipilih
        account_column = selected_level.replace("kd_", "nm_")  # Ubah kd_lv_X menjadi nm_lv_X

        # Multiselect widget untuk memilih Nama Unit atau Sub Unit
        unit_options = ["nm_unit", "nm_sub_unit"]
        selected_unit_type = st.radio("Pilih Tipe Unit", unit_options)
        unique_units = list(df[selected_unit_type].dropna().unique())
        selected_units = st.multiselect(
            f"Pilih {selected_unit_type}", 
            unique_units
        )

        # Multiselect widget untuk filter nama akun sesuai level
        unique_accounts = list(df[account_column].dropna().unique())
        selected_accounts = st.multiselect(
            f"Pilih Nama Akun ({account_column})", 
            unique_accounts
        )

        # Slider untuk memilih rentang bulan
        months = [
            "Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember"
        ]
        month_map = {
            "Januari": 1, "Februari": 2, "Maret": 3, "April": 4,
            "Mei": 5, "Juni": 6, "Juli": 7, "Agustus": 8,
            "September": 9, "Oktober": 10, "November": 11, "Desember": 12
        }
        selected_month_range = st.select_slider(
            "Pilih Rentang Bulan",
            options=months,
            value=("Januari", "Desember")  # Default: Januari hingga Desember
        )

        # Terapkan filter
        filtered_df = df.copy()

        # Filter berdasarkan nama akun
        if selected_accounts:
            filtered_df = filtered_df[filtered_df[account_column].isin(selected_accounts)]

        # Filter berdasarkan nama unit atau sub unit
        if selected_units:
            filtered_df = filtered_df[filtered_df[selected_unit_type].isin(selected_units)]

        # Filter berdasarkan rentang bulan
        start_month = month_map[selected_month_range[0]]
        end_month = month_map[selected_month_range[1]]
        filtered_df = filtered_df[
            (filtered_df['tgl_transaksi'].dt.month >= start_month) &
            (filtered_df['tgl_transaksi'].dt.month <= end_month)
        ]

        # Tampilkan hasil filter
        if not filtered_df.empty:
            st.subheader("Data yang Difilter")
            filtered_df = filtered_df[
                ["nomor", "no_bukti", "tgl_transaksi", selected_unit_type, account_column, "debet", "kredit", "uraian"]
            ]

            # Hitung total debet dan kredit
            total_debet = filtered_df["debet"].sum()
            total_kredit = filtered_df["kredit"].sum()

            # Hitung saldo
            saldo = total_debet - total_kredit
            if saldo > 0:
                saldo_row = {"debet": saldo, "kredit": 0, "uraian": "Saldo"}
            else:
                saldo_row = {"debet": 0, "kredit": abs(saldo), "uraian": "Saldo"}

            # Tambahkan baris saldo ke dataframe
            saldo_df = pd.DataFrame([saldo_row])
            final_df = pd.concat([filtered_df, saldo_df], ignore_index=True)

            # Tampilkan tabel
            st.dataframe(final_df)

            # Download hasil filter sebagai Excel
            @st.cache_data
            def convert_df_to_excel(df):
                output = BytesIO()
                df.to_excel(output, index=False, sheet_name="Filtered_Data", engine="openpyxl")
                output.seek(0)  # Kembalikan pointer ke awal file
                return output.getvalue()

            excel_file = convert_df_to_excel(final_df)
            st.download_button(
                label="Download Data yang Difilter (Excel)",
                data=excel_file,
                file_name="filtered_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Tidak ada data yang sesuai dengan filter.")

else:
    st.warning("Data tidak dapat dimuat. Pastikan file di Google Drive tersedia dan dapat diakses.")
