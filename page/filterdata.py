import streamlit as st
import pandas as pd
from io import BytesIO

def app():
    st.title("Filter Data Transaksi")

    # Baca file hanya sekali dan simpan di session state
    if "bukubesar" not in st.session_state:
        try:
            st.session_state["bukubesar"] = pd.read_excel(
                "data/bukubesar.xlsb",
                engine="pyxlsb"
            )
        except Exception as e:
            st.error(f"Gagal memuat data bukubesar: {str(e)}")
            return

    if "coa" not in st.session_state:
        try:
            st.session_state["coa"] = pd.read_excel("data/coa.xlsx")
        except Exception as e:
            st.error(f"Gagal memuat data coa: {str(e)}")
            return

    # Ambil DataFrame dari session state
    bukubesar = st.session_state["bukubesar"]
    coa = st.session_state["coa"]

    # Perbaiki parsing kolom tgl_transaksi
    try:
        if "tgl_transaksi" in bukubesar.columns:
            # Jika kolom tgl_transaksi berisi nilai numerik (serial Excel)
            if bukubesar["tgl_transaksi"].dtype in ["float64", "int64"]:
                bukubesar["tgl_transaksi"] = pd.to_datetime(
                    bukubesar["tgl_transaksi"], 
                    unit="D", 
                    origin="1899-12-30"
                )
            else:
                # Parsing tanggal dengan format dd/mm/yyyy
                bukubesar["tgl_transaksi"] = pd.to_datetime(
                    bukubesar["tgl_transaksi"],
                    format="%d/%m/%Y",
                    errors="coerce"
                )
        else:
            st.error("Kolom 'tgl_transaksi' tidak ditemukan dalam file bukubesar.")
            return
    except Exception as e:
        st.error(f"Gagal memproses kolom tgl_transaksi: {str(e)}")
        return

    # Inisialisasi session state untuk menyimpan daftar SKPD
    if "skpd_options" not in st.session_state:
        try:
            if "nm_unit" not in bukubesar.columns or bukubesar["nm_unit"].isnull().all():
                raise ValueError("Kolom 'nm_unit' tidak ditemukan atau kosong.")
            
            skpd_options = list(bukubesar["nm_unit"].dropna().unique())
            st.session_state["skpd_options"] = skpd_options
        except Exception as e:
            st.error(f"Gagal memuat daftar SKPD: {str(e)}")
            return

    # Inisialisasi session state untuk menyimpan daftar akun berdasarkan level
    if "level_options" not in st.session_state:
        try:
            if "Level" not in coa.columns or coa["Level"].isnull().all():
                raise ValueError("Kolom 'Level' tidak ditemukan atau kosong.")
            
            level_options = {}
            for level in range(1, 7):
                level_str = f"Level {level}"
                level_options[level_str] = list(
                    coa[coa["Level"] == level]["Nama Akun 6"].unique()
                )
            
            st.session_state["level_options"] = level_options
        except Exception as e:
            st.error(f"Gagal memuat daftar akun: {str(e)}")
            return

    # Widget filtering
    st.subheader("Filter Data")
    st.markdown("---")

    # 1. Filter berdasarkan bulan
    st.write("### Pilih Bulan:")
    selected_month = st.slider("Bulan", min_value=1, max_value=12, value=(1, 12), step=1)
    st.markdown("---")

    # 2. Filter jenis transaksi
    st.write("### Pilih Jenis Transaksi:")
    jenis_transaksi_options = [
        "Jurnal Balik", "Jurnal Koreksi", "Jurnal Non RKUD", "Jurnal Pembiayaan", 
        "Jurnal Penerimaan", "Jurnal Pengeluaran", "Jurnal Penutup", 
        "Jurnal Penyesuaian", "Jurnal Umum", "Saldo Awal"
    ]
    selected_jenis_transaksi = st.multiselect(
        "Jenis Transaksi", options=jenis_transaksi_options, default=jenis_transaksi_options
    )
    st.markdown("---")

    # 3. Filter unit (SKPD atau All)
    st.write("### Pilih Unit:")
    unit_options = ["All", "SKPD"]
    selected_unit = st.radio("Unit", options=unit_options, index=0)
    selected_skpd = None
    if selected_unit == "SKPD":
        if "skpd_options" in st.session_state and st.session_state["skpd_options"]:
            selected_skpd = st.selectbox("Pilih SKPD", options=st.session_state["skpd_options"])
        else:
            st.warning("Daftar SKPD tidak tersedia.")
    st.markdown("---")

    # 4. Filter berdasarkan Kode Level dan Kategori Akun
    st.write("### Pilih Kode Level:")
    level_options = [f"Level {i}" for i in range(1, 7)]
    selected_level = st.selectbox("Kode Level", options=level_options)
    
    st.write("### Pilih Kategori Akun:")
    kategori_akun = {
        "PENDAPATAN DAERAH-LO": "7",
        "BEBAN DAERAH-LO": "8",
        "PENDAPATAN DAERAH": "4",
        "BELANJA DAERAH": "5",
        "PEMBIAYAAN DAERAH": "6",
        "ASET": "1",
        "KEWAJIBAN": "2",
        "EKUITAS": "3"
    }
    selected_kategori = st.selectbox("Kategori Akun", options=list(kategori_akun.keys()))
    
    # Filter akun berdasarkan level dan kategori
    selected_akun = None
    if selected_level:
        target_level = int(selected_level.split()[-1])
        target_kategori = kategori_akun[selected_kategori]
        filtered_akun = coa[
            (coa["Level"] == target_level) & 
            (coa["Kode Akun 6"].astype(str).str.startswith(target_kategori))
        ]["Nama Akun 6"].unique()
        
        if len(filtered_akun) > 0:
            selected_akun = st.selectbox("Pilih Akun:", options=filtered_akun)
        else:
            st.warning("Tidak ada akun tersedia untuk level dan kategori ini.")
    st.markdown("---")

    # 5. Filter berdasarkan Debit/Kredit/All
    st.write("### Pilih Tipe Transaksi:")
    transaction_type = st.radio(
        "Tipe Transaksi", options=["Debet", "Kredit", "All"], horizontal=True
    )
    st.markdown("---")

    # Tombol proses data
    if st.button("Proses Data"):
        try:
            filtered_data = bukubesar.copy()
            
            # 1. Filter bulan
            bulan_condition = (
                (filtered_data["tgl_transaksi"].dt.month >= selected_month[0]) &
                (filtered_data["tgl_transaksi"].dt.month <= selected_month[1])
            )
            filtered_data = filtered_data[bulan_condition]
            
            # 2. Filter jenis transaksi
            filtered_data = filtered_data[filtered_data["jns_transaksi"].isin(selected_jenis_transaksi)]
            
            # 3. Filter unit
            if selected_unit == "SKPD" and selected_skpd:
                filtered_data = filtered_data[filtered_data["nm_unit"] == selected_skpd]
            
            # 4. Filter akun berdasarkan hierarki kode
            if selected_akun:
                target_level = int(selected_level.split()[-1])
                kode_akun = coa[
                    (coa["Nama Akun 6"] == selected_akun) & 
                    (coa["Level"] == target_level)
                ]["Kode Akun 6"].iloc[0]
                
                # Filter kd_lv_6 yang termasuk dalam hierarki kode terpilih
                filtered_data = filtered_data[
                    filtered_data["kd_lv_6"].astype(str).str.startswith(kode_akun)
                ]
            
            # 5. Filter tipe transaksi
            if transaction_type == "Debet":
                filtered_data = filtered_data[filtered_data["debet"] > 0]
            elif transaction_type == "Kredit":
                filtered_data = filtered_data[filtered_data["kredit"] > 0]
            
            # Gabungkan dengan COA untuk tampilkan nama akun
            merged_data = pd.merge(
                filtered_data,
                coa[["Kode Akun 6", "Nama Akun 6"]],
                left_on="kd_lv_6",
                right_on="Kode Akun 6",
                how="left"
            )
            
            # Hitung saldo akun
            saldo_akun = merged_data["debet"].sum() - merged_data["kredit"].sum()
            
            # Tampilkan saldo akun di atas tabel hasil filter
            st.subheader("Saldo Akun")
            st.write(f"Saldo ({selected_akun}): Rp {saldo_akun:,.0f}")
            
            # Generate nama file dinamis
            unit_name = selected_skpd if selected_unit == "SKPD" else "All"
            file_name = f"{unit_name}_{selected_level}_{selected_akun}.xlsx"
            
            # Tampilkan hasil filter
            st.subheader("Hasil Filter")
            top_n = st.number_input("Tampilkan Berapa Baris Teratas?", min_value=1, value=20)
            display_data = merged_data.head(top_n)[[
                "no_bukti", "tgl_transaksi", "jns_transaksi", "nm_unit",
                "kd_lv_6", "Nama Akun 6", "debet", "kredit", "uraian"
            ]]
            st.dataframe(display_data)
            
            # Download hasil
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                merged_data.to_excel(writer, index=False)
            output.seek(0)
            st.download_button(
                "Unduh Excel",
                data=output,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"Terjadi kesalahan: {str(e)}")

# Jalankan aplikasi
app()
