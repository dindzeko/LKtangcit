import streamlit as st
import pandas as pd
from io import BytesIO

def app():
    st.title("Filter Data Transaksi")

    # Inisialisasi session state untuk menyimpan daftar SKPD
    if "skpd_options" not in st.session_state:
        try:
            # Baca file bukubesar.xlsb hanya untuk mendapatkan daftar SKPD
            bukubesar = pd.read_excel("data/bukubesar.xlsb", engine="pyxlsb")
            
            # Pastikan kolom nm_unit ada dan tidak kosong
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
            # Baca file coa.xlsx hanya untuk mendapatkan daftar akun berdasarkan level
            coa = pd.read_excel("data/coa.xlsx")
            
            # Pastikan kolom Level ada dan tidak kosong
            if "Level" not in coa.columns or coa["Level"].isnull().all():
                raise ValueError("Kolom 'Level' tidak ditemukan atau kosong.")
            
            # Kelompokkan akun berdasarkan level (gunakan kolom Level secara langsung)
            level_options = {}
            for level in range(1, 7):
                level_str = f"Level {level}"
                level_options[level_str] = list(
                    coa[coa["Level"] == level]["Nama Akun"].unique()
                )
            
            st.session_state["level_options"] = level_options
        except Exception as e:
            st.error(f"Gagal memuat daftar akun: {str(e)}")
            return

    # Widget filtering
    st.subheader("Filter Data")

    # 1. Filter berdasarkan bulan
    st.write("Pilih Bulan:")
    selected_month = st.slider("Bulan", min_value=1, max_value=12, value=(1, 12), step=1)

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

    # 3. Filter berdasarkan unit (SKPD atau All)
    st.write("Pilih Unit:")
    unit_options = ["All", "SKPD"]
    selected_unit = st.radio("Unit", options=unit_options, index=0)

    # Inisialisasi variabel untuk SKPD
    selected_skpd = None

    if selected_unit == "SKPD":
        # Tampilkan selectbox untuk memilih SKPD
        if "skpd_options" in st.session_state and st.session_state["skpd_options"]:
            selected_skpd = st.selectbox("Pilih SKPD", options=st.session_state["skpd_options"])
        else:
            st.warning("Daftar SKPD tidak tersedia. Silakan periksa file data.")

    # 4. Filter berdasarkan Kode Level (Level 1 sampai Level 6)
    st.write("Pilih Kode Level:")
    level_options = [f"Level {i}" for i in range(1, 7)]
    selected_level = st.selectbox("Kode Level", options=level_options)

    # Tambahkan filter berdasarkan kategori akun
    st.write("Pilih Kategori Akun:")
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

    # Tampilkan selectbox untuk akun berdasarkan level dan kategori yang dipilih
    if selected_level:
        # Pastikan session state level_options memiliki data untuk level yang dipilih
        if selected_level in st.session_state["level_options"]:
            # Filter akun berdasarkan kategori (awalan kode akun)
            coa = pd.read_excel("data/coa.xlsx")
            target_kategori_awalan = kategori_akun[selected_kategori]
            filtered_akun = coa[
                (coa["Level"] == int(selected_level.split()[-1])) &  # Sesuaikan dengan level
                (coa["Kode Akun"].astype(str).str.startswith(target_kategori_awalan))  # Sesuaikan dengan kategori
            ]["Nama Akun"].unique()

            if len(filtered_akun) > 0:  # Pastikan ada opsi akun
                selected_akun = st.selectbox("Pilih Akun:", options=filtered_akun)
            else:
                st.warning(f"Tidak ada akun tersedia untuk {selected_level} dan kategori {selected_kategori}.")
        else:
            st.warning(f"Tidak ada data akun untuk {selected_level}.")

    # 5. Filter berdasarkan Debit/Kredit/All
    st.write("Pilih Tipe Transaksi:")
    transaction_type = st.radio(
        "Tipe Transaksi", options=["Debet", "Kredit", "All"], horizontal=True
    )

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

            # Terapkan filter berdasarkan pilihan pengguna
            filtered_data = merged_data[
                (merged_data["tgl_transaksi"].dt.month >= selected_month[0]) &
                (merged_data["tgl_transaksi"].dt.month <= selected_month[1])
            ]

            # Filter berdasarkan jenis transaksi
            filtered_data = filtered_data[filtered_data["jns_transaksi"].isin(selected_jenis_transaksi)]

            # Filter berdasarkan unit (SKPD atau All)
            if selected_unit == "SKPD":
                # Ambil daftar SKPD unik dari data yang sudah difilter
                filtered_data = filtered_data[filtered_data["nm_unit"] == selected_skpd]

            # Filter berdasarkan Kode Level dan Akun
            if selected_level and selected_akun:
                target_level = int(selected_level.split()[-1])  # Ambil angka dari string "Level X"
                filtered_data = filtered_data[
                    (filtered_data["Level"] == target_level) &  # Gunakan kolom Level secara langsung
                    (filtered_data["Nama Akun"] == selected_akun)
                ]

            # Filter berdasarkan Debit/Kredit/All
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

        except Exception as e:
            st.error(f"Gagal memuat atau memproses data: {str(e)}")

# Panggil fungsi app
app()
untuk filtering aplikasi berjalan works. tapi apakah ada yang harus kita perbaiki agar aplikasi dapat cepat mengkalkulasi 
untuk diketahui data bukubesar memang agak besr filenya 20an mb . dengan tranaksis mencapi 500an rb row .
