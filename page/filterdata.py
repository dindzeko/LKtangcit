import streamlit as st
import pandas as pd
from io import BytesIO

def load_data(file_path):
    """Loads data from an Excel file."""
    try:
        return pd.read_excel(file_path)
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return None
    except Exception as e:
        st.error(f"Error loading data from {file_path}: {e}")
        return None

def app():
    st.title("Filter Data Transaksi")

    # Load data
    bukubesar = load_data("data/bukubesar.xlsb")
    coa = load_data("data/coa.xlsx")

    if bukubesar is None or coa is None:
        return  # Stop if data loading fails

    # Inisialisasi session state untuk menyimpan daftar SKPD
    if "skpd_options" not in st.session_state:
        try:
            st.session_state["skpd_options"] = list(bukubesar["nm_unit"].unique())
        except Exception as e:
            st.error(f"Gagal memuat daftar SKPD: {str(e)}")
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

    selected_skpd = None  # Initialize selected_skpd

    if selected_unit == "SKPD":
        # Tampilkan selectbox untuk memilih SKPD
        selected_skpd = st.selectbox("Pilih SKPD", options=st.session_state["skpd_options"])

    # 4. Filter berdasarkan Kode Level (Level 1 sampai Level 6)
    st.write("Pilih Kode Level:")
    level_options = [f"Level {i}" for i in range(1, 7)]
    selected_level = st.selectbox("Kode Level", options=level_options)

    # Ambil angka dari string "Level X"
    target_level = int(selected_level.split()[-1])

    # Tambahkan filter untuk nama akun berdasarkan level yang dipilih
    level_column = f"Level {target_level}"
    if level_column in coa.columns:
        level_options = list(coa[level_column].dropna().unique()) # Ambil value unik yang tidak NaN
        selected_level_value = st.selectbox(f"Pilih {level_column}:", options=level_options)
    else:
        st.warning(f"Kolom {level_column} tidak ditemukan di file coa.xlsx.")
        selected_level_value = None

    # 5. Filter berdasarkan Debit/Kredit/All
    st.write("Pilih Tipe Transaksi:")
    transaction_type = st.radio(
        "Tipe Transaksi", options=["Debet", "Kredit", "All"], horizontal=True
    )

    # Tombol untuk memproses data
    if st.button("Proses Data"):
        try:
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
                filtered_data = filtered_data[filtered_data["nm_unit"] == selected_skpd]

            # Filter berdasarkan level
            if selected_level_value: #Pastikan ada level yang dipilih user
               filtered_data = filtered_data[filtered_data[level_column].isin([selected_level_value])]

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

if __name__ == "__main__":
    app()
