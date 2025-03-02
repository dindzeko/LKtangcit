import pandas as pd
import streamlit as st
from io import StringIO
import requests

# Judul aplikasi
st.title("Aplikasi Visualisasi Data Transaksi")

# ID file Google Drive (Anda perlu mengganti ini dengan ID file Anda)
file_id = "your-file-id"  # Ganti dengan ID file Google Drive Anda
url = f"https://drive.google.com/file/d/1p2PYISBdkAdFIFf41chb5ltw39L35ztP/view?usp=drive_link"

# Fungsi untuk membaca data dari Google Drive
@st.cache_data
def load_data():
    try:
        # Unduh file dari Google Drive
        response = requests.get(url)
        if response.status_code == 200:
            data = StringIO(response.text)
            df = pd.read_csv(data)
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
    menu = st.sidebar.selectbox("Menu", ["Data Lengkap", "Filter Data", "Visualisasi"])

    # Menu 1: Data Lengkap
    if menu == "Data Lengkap":
        st.header("Data Lengkap")
        st.dataframe(df)

    # Menu 2: Filter Data
    elif menu == "Filter Data":
        st.header("Filter Data")

        # Filter berdasarkan kolom tertentu
        filter_columns = [
            "jns_transaksi", "kd_unit", "nm_unit", "kd_sub_unit", "nm_sub_unit",
            "kd_lv_1", "nm_lv_1", "kd_lv_2", "nm_lv_2", "kd_lv_3", "nm_lv_3",
            "kd_lv_4", "nm_lv_4", "kd_lv_5", "nm_lv_5", "kd_lv_6", "nm_lv_6"
        ]

        filters = {}
        for col in filter_columns:
            unique_values = ["Semua"] + list(df[col].dropna().unique())
            selected_value = st.selectbox(f"Pilih {col}", unique_values)
            if selected_value != "Semua":
                filters[col] = selected_value

        # Terapkan filter
        filtered_df = df.copy()
        for col, value in filters.items():
            filtered_df = filtered_df[filtered_df[col] == value]

        # Tampilkan hasil filter
        if not filtered_df.empty:
            st.subheader("Data yang Difilter")
            filtered_df = filtered_df[["debet", "kredit", "uraian"]]

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

            # Download hasil filter sebagai CSV
            @st.cache_data
            def convert_df_to_csv(df):
                return df.to_csv(index=False).encode('utf-8')

            csv = convert_df_to_csv(final_df)
            st.download_button(
                label="Download Data yang Difilter",
                data=csv,
                file_name="filtered_data.csv",
                mime="text/csv"
            )
        else:
            st.warning("Tidak ada data yang sesuai dengan filter.")

    # Menu 3: Visualisasi
    elif menu == "Visualisasi":
        st.header("Visualisasi Data")

        # Pie chart untuk distribusi debet dan kredit
        total_debet = df["debet"].sum()
        total_kredit = df["kredit"].sum()

        st.subheader("Distribusi Debet dan Kredit")
        fig, ax = plt.subplots()
        ax.pie([total_debet, total_kredit], labels=["Debet", "Kredit"], autopct="%1.1f%%", startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        st.pyplot(fig)

        # Bar chart untuk total transaksi per unit
        st.subheader("Total Transaksi per Unit")
        total_per_unit = df.groupby("kd_unit")[["debet", "kredit"]].sum().reset_index()
        fig, ax = plt.subplots()
        total_per_unit.plot(kind="bar", x="kd_unit", ax=ax)
        ax.set_title("Total Debet dan Kredit per Unit")
        ax.set_xlabel("Kode Unit")
        ax.set_ylabel("Jumlah")
        st.pyplot(fig)

else:
    st.warning("Data tidak dapat dimuat. Pastikan URL Google Drive valid.")
