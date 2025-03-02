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

# Fungsi untuk membaca data dari Google Drive dengan optimasi
@st.cache_data
def load_data():
    try:
        # Tentukan tipe data kolom untuk optimasi memori
        dtype = {
            'nomor': 'category',
            'no_bukti': 'category',
            'nm_unit': 'category',
            'nm_sub_unit': 'category',
            'kd_lv_1': 'category',
            'kd_lv_2': 'category',
            'kd_lv_3': 'category',
            'kd_lv_4': 'category',
            'kd_lv_5': 'category',
            'kd_lv_6': 'category',
            'nm_lv_1': 'category',
            'nm_lv_2': 'category',
            'nm_lv_3': 'category',
            'nm_lv_4': 'category',
            'nm_lv_5': 'category',
            'nm_lv_6': 'category',
            'debet': 'float32',
            'kredit': 'float32'
        }

        # Unduh file dari Google Drive
        response = requests.get(url)
        if response.status_code == 200:
            data = BytesIO(response.content)
            df = pd.read_csv(
                data,
                sep=',',
                encoding='utf-8',
                dtype=dtype,
                parse_dates=['tgl_transaksi'],
                infer_datetime_format=True
            )
            
            # Tambahkan kolom bulan untuk filter lebih cepat
            df['bulan'] = df['tgl_transaksi'].dt.month
            return df
        else:
            st.error(f"Gagal memuat data. Status code: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error saat memuat data: {e}")
        return None

# Memuat data dengan optimasi
df = load_data()

# Fungsi untuk filter data yang digunakan bersama
def apply_filters(data, selected_unit_type, selected_units, account_column, selected_accounts, month_range):
    filtered = data
    
    # Filter unit
    if selected_units:
        filtered = filtered[filtered[selected_unit_type].isin(selected_units)]
    
    # Filter akun
    if selected_accounts:
        filtered = filtered[filtered[account_column].isin(selected_accounts)]
    
    # Filter bulan
    if month_range:
        start_month, end_month = month_range
        filtered = filtered[(filtered['bulan'] >= start_month) & (filtered['bulan'] <= end_month)]
    
    return filtered

# Fungsi untuk komponen UI filter yang digunakan bersama
def filter_ui():
    # Radio button untuk memilih kode level
    level_options = ["kd_lv_1", "kd_lv_2", "kd_lv_3", "kd_lv_4", "kd_lv_5", "kd_lv_6"]
    selected_level = st.radio("Pilih Kode Level", level_options)
    
    # Tentukan nama akun berdasarkan level yang dipilih
    account_column = selected_level.replace("kd_", "nm_")
    
    # Radio button untuk memilih tipe unit
    unit_options = ["nm_unit", "nm_sub_unit"]
    selected_unit_type = st.radio("Pilih Tipe Unit", unit_options)
    
    # Multiselect widget untuk filter unit/sub unit
    unique_units = df[selected_unit_type].cat.categories.tolist()
    selected_units = st.multiselect(
        f"Pilih {selected_unit_type}", 
        unique_units
    )
    
    # Multiselect widget untuk filter nama akun
    unique_accounts = df[account_column].cat.categories.tolist()
    selected_accounts = st.multiselect(
        f"Pilih Nama Akun ({account_column})", 
        unique_accounts
    )
    
    # Slider untuk memilih rentang bulan
    month_map = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    
    selected_month_range = st.select_slider(
        "Pilih Rentang Bulan",
        options=list(month_map.keys()),
        format_func=lambda x: month_map[x],
        value=(1, 12)
    )
    
    return {
        'selected_level': selected_level,
        'account_column': account_column,
        'selected_unit_type': selected_unit_type,
        'selected_units': selected_units,
        'selected_accounts': selected_accounts,
        'month_range': selected_month_range
    }

if df is not None:
    # Sidebar untuk navigasi
    menu = st.sidebar.selectbox("Menu", ["Filter Data", "Visualisasi"])

    # Dapatkan parameter filter dari UI
    filter_params = filter_ui()
    
    # Terapkan filter
    filtered_df = apply_filters(
        df,
        filter_params['selected_unit_type'],
        filter_params['selected_units'],
        filter_params['account_column'],
        filter_params['selected_accounts'],
        filter_params['month_range']
    )

    if menu == "Filter Data":
        st.header("Filter Data")

        if not filtered_df.empty:
            # Tampilkan data yang difilter
            st.subheader("Data yang Difilter")
            display_columns = ["nomor", "no_bukti", "tgl_transaksi", 
                             filter_params['selected_unit_type'], 
                             filter_params['account_column'], 
                             "debet", "kredit", "uraian"]
            
            # Hitung total debet dan kredit
            total_debet = filtered_df["debet"].sum()
            total_kredit = filtered_df["kredit"].sum()
            
            # Tampilkan data dengan totals
            st.dataframe(filtered_df[display_columns])
            
            # Tampilkan total
            col1, col2 = st.columns(2)
            col1.metric("Total Debet", f"Rp{total_debet:,.2f}")
            col2.metric("Total Kredit", f"Rp{total_kredit:,.2f}")
            st.metric("Saldo", f"Rp{total_debet - total_kredit:,.2f}")

            # Download hasil filter
            @st.cache_data
            def convert_df_to_excel(df):
                return df[display_columns].to_excel(index=False)

            st.download_button(
                label="Download Data yang Difilter (Excel)",
                data=convert_df_to_excel(filtered_df),
                file_name="filtered_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Tidak ada data yang sesuai dengan filter.")

    elif menu == "Visualisasi":
        st.header("Visualisasi Data")

        if not filtered_df.empty:
            # Optimasi visualisasi dengan native Streamlit
            st.subheader("Top 5 Jenis Nama Kode Belanja Terbanyak")
            top_belanja = filtered_df.groupby(filter_params['account_column'])["debet"].sum().nlargest(5)
            st.bar_chart(top_belanja)

            st.subheader("Top 5 Nama Unit/Sub Unit dengan Realisasi Terbesar")
            top_unit_realisasi = filtered_df.groupby(filter_params['selected_unit_type'])["debet"].sum().nlargest(5)
            st.bar_chart(top_unit_realisasi)

            st.subheader("Top 5 Nama Unit/Sub Unit dengan Jumlah Transaksi Terbanyak")
            top_unit_transaksi = filtered_df[filter_params['selected_unit_type']].value_counts().nlargest(5)
            st.bar_chart(top_unit_transaksi)
        else:
            st.warning("Tidak ada data yang sesuai dengan filter.")

else:
    st.warning("Data tidak dapat dimuat. Pastikan file di Google Drive tersedia dan dapat diakses.")
