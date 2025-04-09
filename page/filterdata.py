import streamlit as st
import pandas as pd
from io import BytesIO

def app():
    st.title("Filter Data Transaksi")

    # ================== DATA LOADING ==================
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
            # Konversi semua kode akun ke string
            for col in st.session_state["coa"].columns:
                if 'Kode Akun' in col:
                    st.session_state["coa"][col] = st.session_state["coa"][col].astype(str).str.strip()
        except Exception as e:
            st.error(f"Gagal memuat data coa: {str(e)}")
            return

    bukubesar = st.session_state["bukubesar"]
    coa = st.session_state["coa"]

    # ================== PREPROCESSING ==================
    try:
        if "tgl_transaksi" in bukubesar.columns:
            bukubesar["tgl_transaksi"] = pd.to_datetime(
                bukubesar["tgl_transaksi"], 
                errors="coerce"
            )
            bukubesar = bukubesar.dropna(subset=["tgl_transaksi"])
        else:
            st.error("Kolom 'tgl_transaksi' tidak ditemukan")
            return
    except Exception as e:
        st.error(f"Gagal memproses tanggal: {str(e)}")
        return

    # ================== LEVEL 1 CATEGORIES ==================
    level1_mapping = {
        '1': 'ASET',
        '2': 'KEWAJIBAN',
        '3': 'EKUITAS', 
        '4': 'PENDAPATAN DAERAH',
        '5': 'BELANJA DAERAH',
        '6': 'PEMBIAYAAN DAERAH',
        '7': 'PENDAPATAN DAERAH-LO',
        '8': 'BEBAN DAERAH'
    }

    # ================== WIDGET FILTER ==================
    st.subheader("Filter Data")
    st.markdown("---")

    # 1. Filter Unit
    st.write("### Pilih Unit:")
    selected_unit = st.radio("Unit", ["All", "SKPD"], index=0)
    selected_skpd = None
    if selected_unit == "SKPD":
        skpd_options = bukubesar["nm_unit"].unique()
        selected_skpd = st.selectbox("Pilih SKPD", skpd_options)
    st.markdown("---")

    # 2. Filter Level Akun
    st.write("### Pilih Level Akun:")
    selected_level = st.selectbox("Level", options=[f"Level {i}" for i in range(1, 7)])
    target_level = int(selected_level.split()[-1])
    st.markdown("---")

    # 3. Filter Kategori Akun
    st.write("### Pilih Kategori Akun:")
    
    if target_level == 1:
        # Khusus Level 1 menggunakan mapping tetap
        kategori_options = list(level1_mapping.values())
        selected_kategori = st.selectbox("Kategori", options=kategori_options)
        
        # Dapatkan kode awalan dari mapping
        selected_kode = [k for k, v in level1_mapping.items() if v == selected_kategori][0]
    else:
        # Untuk level 2-6 ambil dari struktur COA
        parent_level = target_level - 1
        parent_col = f"Kode Akun {parent_level}"
        
        # Validasi struktur hierarki
        if parent_col not in coa.columns:
            st.error(f"Struktur COA tidak valid untuk level {target_level}")
            return
        
        # Ambil kategori berdasarkan level parent
        kategori_options = coa[[parent_col, f"Nama Akun {parent_level}"]]
        kategori_options = kategori_options.drop_duplicates().dropna()
        
        selected_parent = st.selectbox(
            "Kategori Induk",
            options=kategori_options[f"Nama Akun {parent_level}"]
        )
        
        # Dapatkan kode parent
        selected_kode = kategori_options[
            kategori_options[f"Nama Akun {parent_level}"] == selected_parent
        ][parent_col].iloc[0]

    st.markdown("---")

    # 4. Filter Akun Spesifik
    st.write("### Pilih Akun:")
    target_col = f"Kode Akun {target_level}"
    
    # Filter berdasarkan kode parent
    filtered_coa = coa[coa[target_col].str.startswith(selected_kode)]
    akun_options = filtered_coa[f"Nama Akun {target_level}"].unique()
    
    if len(akun_options) > 0:
        selected_akun = st.selectbox("Nama Akun", akun_options)
        kode_akun = filtered_coa[
            filtered_coa[f"Nama Akun {target_level}"] == selected_akun
        ][target_col].iloc[0]
    else:
        st.warning("Tidak ada akun tersedia")
        return
    
    st.markdown("---")

    # ================== PROCESS DATA ==================
    if st.button("Proses Data"):
        try:
            # Filter dasar
            filtered_data = bukubesar[
                (bukubesar["kd_lv_6"].str.startswith(kode_akun)) &
                (bukubesar["jns_transaksi"].notna())
            ]
            
            # Filter tambahan
            if selected_unit == "SKPD" and selected_skpd:
                filtered_data = filtered_data[filtered_data["nm_unit"] == selected_skpd]
            
            # Gabungkan dengan data COA
            merged_data = pd.merge(
                filtered_data,
                coa[["Kode Akun 6", "Nama Akun 6"]],
                left_on="kd_lv_6",
                right_on="Kode Akun 6",
                how="left"
            )
            
            # Tampilkan hasil
            st.subheader("Hasil Filter")
            st.dataframe(merged_data.head())
            
            # Download
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                merged_data.to_excel(writer, index=False)
            output.seek(0)
            
            st.download_button(
                "Unduh Data",
                data=output,
                file_name=f"data_{selected_kategori}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"Terjadi kesalahan: {str(e)}")

app()
