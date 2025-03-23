import streamlit as st
import pandas as pd
from io import BytesIO

def app():
    st.title("Halaman Filter Data")

    # Load data
    try:
        # Baca file bukubesar.xlsb dari folder data/
        bukubesar = pd.read_excel("data/bukubesar.xlsb", engine="pyxlsb")
        # Baca file coa.xlsx dari folder data/
        coa = pd.read_excel("data/coa.xlsx")
        
        # Membersihkan nama kolom dari spasi atau karakter khusus
        bukubesar.columns = bukubesar.columns.str.replace(r"\s+", " ", regex=True).str.strip()
        coa.columns = coa.columns.str.replace(r"\s+", " ", regex=True).str.strip()

        # Gabungkan data berdasarkan kd_lv_6 dan Kode Akun
        merged_data = pd.merge(bukubesar, coa, left_on="kd_lv_6", right_on="Kode Akun", how="left")
    except Exception as e:
        st.error(f"Gagal memuat data: {str(e)}")
        return

    # Cek kolom penting
    required_columns = ["Level", "debet", "kredit", "jns_transaksi", "nm_unit"]
    missing_columns = [col for col in required_columns if col not in merged_data.columns]
    if missing_columns:
        st.error(f"Kolom berikut tidak ditemukan dalam dataset: {', '.join(missing_columns)}. "
                 "Pastikan file Excel memiliki kolom tersebut.")
        return

    # Pastikan kolom tgl_transaksi adalah datetime
    try:
        merged_data["tgl_transaksi"] = pd.to_datetime(merged_data["tgl_transaksi"], errors="coerce")
    except Exception as e:
        st.error(f"Gagal mengonversi kolom tgl_transaksi ke datetime: {str(e)}")
        return

    # Widget filtering
    st.subheader("Filtering Data")

    # 1. Filter berdasarkan bulan
    st.write("Pilih Bulan:")
    selected_month = st.slider("Bulan", min_value=1, max_value=12, value=(1, 12), step=1)
    filtered_data = merged_data[
        (merged_data["tgl_transaksi"].dt.month >= selected_month[0]) &
        (merged_data["tgl_transaksi"].dt.month <= selected_month[1])
    ]

    # 2. Filter berdasarkan jenis transaksi
    st.write("Pilih Jenis Transaksi:")
    jenis_transaksi_options = [
        "Jurnal Balik", "Jurnal Koreksi", "Jurnal Non RKUD", "Jurnal Pembiayaan", 
        "Jurnal Penerimaan", "Jurnal Pengeluaran", "Jurnal Penutup", 
        "Jurnal Penyesuaian", "Jurnal Umum", "Saldo Awal"
    ]
    selected_jenis_transaksi = st.multiselect(
        "Jenis Transaksi", options=jenis_transaksi_options, default=jenis_transaksi_options
    )
    filtered_data = filtered_data[filtered_data["jns_transaksi"].isin(selected_jenis_transaksi)]

    # 3. Filter berdasarkan unit (SKPD atau All)
    st.write("Pilih Unit:")
    unit_options = ["All", "SKPD"]
    selected_unit = st.radio("Unit", options=unit_options, index=0)

    if selected_unit == "SKPD":
        # Tampilkan filter untuk memilih SKPD
        skpd_options = list(filtered_data["nm_unit"].unique())
        selected_skpd = st.selectbox("Pilih SKPD", options=skpd_options)
        filtered_data = filtered_data[filtered_data["nm_unit"] == selected_skpd]

    # 4. Filter berdasarkan Kode Level (select box)
    st.write("Pilih Kode Level:")
    level_options = [f"Level {i}" for i in range(1, 7)]
    selected_level = st.selectbox("Kode Level", options=level_options)
    
    # Hitung jumlah titik desimal untuk filter level
    target_level = int(selected_level.split()[-1])  # Ambil angka dari string "Level X"
    filtered_data = filtered_data[
        filtered_data["Level"].apply(lambda x: str(x).count(".") == target_level - 1)
    ]

    # 5. Filter berdasarkan Debit/Kredit/All (tags)
    st.write("Pilih Tipe Transaksi:")
    transaction_type = st.radio(
        "Tipe Transaksi", options=["Debet", "Kredit", "All"], horizontal=True
    )
    if transaction_type == "Debet":
        filtered_data = filtered_data[filtered_data["debet"] > 0]
    elif transaction_type == "Kredit":
        filtered_data = filtered_data[filtered_data["kredit"] > 0]

    # Display hasil filter
    st.subheader("Hasil Filter")
    top_n = st.number_input("Tampilkan Berapa Baris Teratas?", min_value=1, max_value=100, value=20)
    display_data = filtered_data.head(top_n) if len(filtered_data) > top_n else filtered_data
    st.dataframe(display_data)

    # Download hasil filter sebagai Excel
    st.subheader("Download Hasil Filter")
    if st.button("Download Excel"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            display_data.to_excel(writer, index=False, sheet_name="Filtered Data")
        output.seek(0)
        st.download_button(
            label="Unduh File Excel",
            data=output,
            file_name="filtered_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
