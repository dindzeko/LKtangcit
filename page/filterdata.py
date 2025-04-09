import pandas as pd
import streamlit as st

# Fungsi utama
def main():
    # Judul aplikasi
    st.title("Filter Data Berdasarkan Hierarki Akun COA")

    # Upload file COA
    uploaded_file = st.file_uploader("Upload File COA (CSV)", type=["csv"])
    if uploaded_file is not None:
        coa = pd.read_csv(uploaded_file)

        # Validasi format COA
        required_columns = [f"Kode Akun {i}" for i in range(1, 7)] + [f"Nama Akun {i}" for i in range(1, 7)]
        if any(col not in coa.columns for col in required_columns):
            st.error("Format COA tidak valid. Pastikan kolom Kode Akun dan Nama Akun 1-6 ada.")
            return

        # 1. Pilih Jenis Laporan
        st.write("### Pilih Jenis Laporan:")
        jenis_laporan = {
            "1": "ASET",
            "2": "KEWAJIBAN",
            "3": "EKUITAS",
            "4": "PENDAPATAN DAERAH",
            "5": "BELANJA DAERAH",
            "6": "PEMBIAYAAN DAERAH",
            "7": "PENDAPATAN DAERAH-LO",
            "8": "BEBAN DAERAH"
        }
        selected_jenis = st.selectbox("Jenis Laporan", options=jenis_laporan.keys(), format_func=lambda x: f"{x} - {jenis_laporan[x]}")

        # Filter data berdasarkan jenis laporan (Level 1)
        level_col = "Kode Akun 1"
        name_col = "Nama Akun 1"

        if level_col not in coa.columns or name_col not in coa.columns:
            st.error(f"Kolom {level_col} atau {name_col} tidak ditemukan!")
            return

        filtered_coa = coa[
            (coa[level_col].astype(str).str.strip() == selected_jenis) &
            (coa[name_col].notna())
        ]

        if filtered_coa.empty:
            st.error(f"Tidak ditemukan data untuk jenis laporan: {jenis_laporan[selected_jenis]}")
            return

        # 2. Pilih Level Akun
        st.write("### Pilih Level Akun:")
        level_options = [f"Level {i}" for i in range(1, 7)]
        selected_level = st.selectbox("Level Akun", options=level_options)

        # 3. Pilih Kategori Akun
        st.write("### Pilih Kategori Akun:")
        target_level = int(selected_level.split()[-1])
        level_col = f"Kode Akun {target_level}"
        name_col = f"Nama Akun {target_level}"

        # Validasi kolom
        if level_col not in coa.columns or name_col not in coa.columns:
            st.error(f"Kolom {level_col} atau {name_col} tidak ditemukan!")
            return

        # Ambil kategori akun berdasarkan hierarki
        kategori_akun = filtered_coa[
            (filtered_coa[level_col].notna()) & 
            (filtered_coa[name_col].notna())
        ][[level_col, name_col]].drop_duplicates()

        # Konversi ke string dan strip whitespace
        kategori_akun[level_col] = kategori_akun[level_col].astype(str).str.strip()
        kategori_akun[name_col] = kategori_akun[name_col].str.strip()

        if kategori_akun.empty:
            st.error(f"Tidak ditemukan kategori akun untuk Level {target_level}.")
            return

        selected_kategori = st.selectbox("Kategori Akun", options=kategori_akun[name_col])

        # Dapatkan kode akun yang sesuai
        selected_kode = kategori_akun[
            kategori_akun[name_col] == selected_kategori
        ][level_col].iloc[0]

        # Filter akun level 6 berdasarkan hierarki
        filtered_akun = coa[
            (coa[level_col].astype(str).str.startswith(str(selected_kode).strip())) &
            (coa["Nama Akun 6"].notna())
        ]["Nama Akun 6"].unique()

        # Tampilkan hasil
        st.write("### Daftar Akun Level 6:")
        st.write(filtered_akun)

# Jalankan aplikasi
if __name__ == "__main__":
    main()
