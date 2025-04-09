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

    # Inisialisasi session state untuk menyimpan daftar akun berdasarkan level
    if "level_options" not in st.session_state:
        try:
            # Pastikan kolom-kolom yang diperlukan ada di DataFrame coa
            required_columns = [f"Kode Akun {i}" for i in range(1, 7)]
            if any(col not in coa.columns for col in required_columns):
                raise ValueError("Kolom 'Kode Akun' tidak ditemukan.")

            level_options = {}
            for level in range(1, 7):
                level_col = f"Kode Akun {level}"
                name_col = f"Nama Akun {level}"
                
                # Dapatkan daftar kategori akun untuk level tertentu
                level_options[f"Level {level}"] = list(
                    coa[[level_col, name_col]].drop_duplicates()[name_col]
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

    # 4. Filter berdasarkan Level Akun
    st.write("### Pilih Level Akun:")
    level_options = [f"Level {i}" for i in range(1, 7)]
    selected_level = st.selectbox("Level Akun", options=level_options)

    # 5. Filter berdasarkan Kategori Akun
    st.write("### Pilih Kategori Akun:")
    target_level = int(selected_level.split()[-1])
    level_col = f"Kode Akun {target_level}"
    name_col = f"Nama Akun {target_level}"
    
    # Validasi kolom level yang dipilih
    if level_col not in coa.columns:
        st.error(f"Kolom '{level_col}' tidak ditemukan dalam file COA.")
        return
    
    # Daftar kategori akun berdasarkan level yang dipilih
    kategori_akun = coa[[level_col, name_col]].drop_duplicates()
    selected_kategori = st.selectbox("Kategori Akun", options=kategori_akun[name_col])

    # Dapatkan kode akun yang sesuai dengan kategori yang dipilih
    selected_kode = kategori_akun[kategori_akun[name_col] == selected_kategori][level_col].iloc[0]

    # Filter akun berdasarkan level dan kategori
    filtered_akun = coa[
        coa[level_col].astype(str).str.startswith(selected_kode)
    ]["Nama Akun 6"].unique()

    if len(filtered_akun) > 0:
        selected_akun = st.selectbox("Pilih Akun:", options=filtered_akun)
    else:
        st.warning("Tidak ada akun tersedia untuk level dan kategori ini.")
    st.markdown("---")

    # 6. Filter berdasarkan Debit/Kredit/All
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
            
            # 4. Filter akun berdasarkan kategori
            if selected_akun:
                kode_akun = coa[
                    coa["Nama Akun 6"] == selected_akun
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
