import streamlit as st
import pandas as pd
from io import BytesIO

def app():
    st.title("Filter Data Transaksi")

    # Inisialisasi session state untuk menyimpan data hasil penggabungan
    if "merged_data" not in st.session_state:
        st.session_state["merged_data"] = None

    # Tombol untuk memproses data
    if st.button("Proses Data"):
        try:
            # Baca file bukubesar.xlsb (data transaksi)
            bukubesar = pd.read_excel("data/bukubesar.xlsb", engine="pyxlsb")
            # Baca file coa.xlsx (data COA untuk nama akun)
            coa = pd.read_excel("data/coa.xlsx")
            
            # Gabungkan data berdasarkan kd_lv_6 dan Kode Akun
            merged_data = pd.merge(bukubesar, coa, left_on="kd_lv_6", right_on="Kode Akun", how="left")
            
            # Pastikan kolom tgl_transaksi adalah datetime
            merged_data["tgl_transaksi"] = pd.to_datetime(merged_data["tgl_transaksi"], errors="coerce")
            
            # Simpan data hasil penggabungan ke session state
            st.session_state["merged_data"] = merged_data
            st.success("Data berhasil diproses!")
        except Exception as e:
            st.error(f"Gagal memuat atau memproses data: {str(e)}")

    # Cek apakah data sudah diproses
    if st.session_state["merged_data"] is None:
        st.warning("Silakan tekan tombol 'Proses Data' untuk memulai.")
        return

    # Ambil data hasil penggabungan dari session state
    filtered_data = st.session_state["merged_data"].copy()

    # Widget filtering
    st.subheader("Filter Data")

    # 1. Filter berdasarkan bulan
    st.write("Pilih Bulan:")
    selected_month = st.slider("Bulan", min_value=1, max_value=12, value=(1, 12), step=1)
    filtered_data = filtered_data[
        (filtered_data["tgl_transaksi"].dt.month >= selected_month[0]) &
        (filtered_data["tgl_transaksi"].dt.month <= selected_month[1])
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

    # 4. Filter berdasarkan Kode Level (Level 1 sampai Level 6)
    st.write("Pilih Kode Level:")
    level_options = [f"Level {i}" for i in range(1, 7)]
    selected_level = st.selectbox("Kode Level", options=level_options)
    
    # Hitung jumlah titik desimal untuk filter level
    target_level = int(selected_level.split()[-1])  # Ambil angka dari string "Level X"
    filtered_data = filtered_data[
        filtered_data["Level"].apply(lambda x: str(x).count(".") == target_level - 1)
    ]

    # 5. Filter berdasarkan Debit/Kredit/All
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

    # Hanya tampilkan kolom penting untuk pengguna
    columns_to_display = [
        "no_bukti", "tgl_transaksi", "jns_transaksi", "nm_unit", "kd_lv_6", 
        "Nama Akun", "debet", "kredit", "uraian"
    ]
    display_data = display_data[columns_to_display]
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
