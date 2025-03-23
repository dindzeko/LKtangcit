import streamlit as st
import pandas as pd
from io import BytesIO

@st.cache_data  # Gunakan st.cache_data untuk menyimpan data yang telah di-load
def load_data():
    try:
        # Baca file bukubesar.xlsb (data transaksi)
        bukubesar = pd.read_excel("data/bukubesar.xlsb", engine="pyxlsb")
        # Baca file coa.xlsx (data COA untuk nama akun)
        coa = pd.read_excel("data/coa.xlsx")

        # Gabungkan data berdasarkan kd_lv_6 dan Kode Akun
        merged_data = pd.merge(bukubesar, coa, left_on="kd_lv_6", right_on="Kode Akun", how="left")

        # Pastikan kolom tgl_transaksi adalah datetime
        merged_data["tgl_transaksi"] = pd.to_datetime(merged_data["tgl_transaksi"], errors="coerce")

        return merged_data
    except FileNotFoundError as e:
        st.error(f"File tidak ditemukan: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Gagal memuat data: {str(e)}")
        return None


def app():
    st.title("Filter Data Transaksi")

    # Load data
    merged_data = load_data()

    if merged_data is None:
        return  # Hentikan aplikasi jika data gagal dimuat

    # Widget filtering
    st.subheader("Filter Data")

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
    unit_options = ["All"] + list(merged_data["nm_unit"].unique())  # Tambahkan "All" ke daftar SKPD
    selected_unit = st.selectbox("Unit", options=unit_options, index=0)  # Gunakan selectbox

    if selected_unit != "All":
        filtered_data = filtered_data[filtered_data["nm_unit"] == selected_unit]

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
    if len(filtered_data) == 0:
        st.warning("Tidak ada data yang sesuai dengan kriteria filter yang dipilih.")
    else:
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


if __name__ == "__main__":
    app()
