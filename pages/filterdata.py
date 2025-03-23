import streamlit as st
from streamlit_option_menu import option_menu

# Impor modul untuk halaman Filter Data
try:
    from filterdata import app as filterdata_app  # Mengimpor fungsi app dari filterdata.py
except ImportError as e:
    st.error(f"Error importing modules: {str(e)}")
    st.stop()

# ----------- HALAMAN UTAMA -----------
def main_page():
    st.title("Selamat Datang!")
    st.write("""
    Aplikasi ini dirancang untuk membantu Anda mengelola laporan keuangan.
    Pilih halaman dari menu sidebar untuk melihat laporan tertentu.
    
    Halaman yang tersedia:
    - **Filter Data**: Memfilter data transaksi.
    - **LRA**: Laporan Realisasi Anggaran.
    - **Neraca**: Laporan Neraca.
    - **LO**: Laporan Operasional.
    - **Prosedur Analitis**: Melakukan analisis prosedural.
    """)

# ----------- HALAMAN FILTER DATA -----------
def filter_data_page():
    # Panggil fungsi app dari filterdata.py
    filterdata_app()

# ----------- HALAMAN LRA -----------
def lra_page():
    st.title("Halaman LRA")
    st.write("Ini adalah halaman untuk Laporan Realisasi Anggaran (LRA).")
    tahun = st.selectbox("Pilih Tahun:", ["2021", "2022", "2023"])
    st.write(f"Menampilkan data LRA untuk tahun {tahun}.")
    # Contoh: Tampilkan grafik atau tabel LRA (akan ditambahkan nanti)

# ----------- HALAMAN NERACA -----------
def neraca_page():
    st.title("Halaman Neraca")
    st.write("Ini adalah halaman untuk Laporan Neraca.")
    periode = st.radio("Pilih Periode:", ["Bulan", "Tahun"])
    st.write(f"Menampilkan data neraca untuk periode {periode}.")
    # Contoh: Tampilkan neraca dalam bentuk tabel atau grafik (akan ditambahkan nanti)

# ----------- HALAMAN LO -----------
def lo_page():
    st.title("Halaman LO")
    st.write("Ini adalah halaman untuk Laporan Operasional (LO).")
    jenis_laporan = st.multiselect("Pilih Jenis Laporan:", ["Pendapatan", "Beban", "Laba Rugi"])
    st.write(f"Menampilkan data LO untuk kategori: {', '.join(jenis_laporan)}.")
    # Contoh: Tampilkan laporan operasional (akan ditambahkan nanti)

# ----------- HALAMAN PROSEDUR ANALITIS -----------
def prosedur_analitis_page():
    st.title("Halaman Prosedur Analitis")
    st.write("Ini adalah halaman untuk melakukan analisis prosedural.")
    metode_analisis = st.selectbox("Pilih Metode Analisis:", ["Analisis Varians", "Analisis Trend", "Analisis Rasio"])
    st.write(f"Melakukan {metode_analisis}...")
    # Contoh: Tambahkan logika analisis (akan ditambahkan nanti)

# ----------- KONFIGURASI NAVIGASI -----------
page_config = {
    "Main Page": main_page,
    "Filter Data": filter_data_page,
    "LRA": lra_page,
    "Neraca": neraca_page,
    "LO": lo_page,
    "Prosedur Analitis": prosedur_analitis_page,
}

# ----------- SIDEBAR -----------
with st.sidebar:
    selected = option_menu(
        menu_title="Menu Navigasi",  # Judul menu
        options=["Main Page", "Filter Data", "LRA", "Neraca", "LO", "Prosedur Analitis"],  # Opsi menu
        icons=["house", "funnel", "bar-chart", "clipboard-data", "file-earmark-text", "gear"],  # Ikon untuk setiap opsi
        menu_icon="cast",  # Ikon utama untuk menu
        default_index=0,  # Halaman default saat aplikasi dimuat
        styles={
            "container": {"padding": "5px"},
            "icon": {"color": "orange", "font-size": "20px"}, 
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "10px",
                "--hover-color": "#0078d4",  # Warna hover
            },
            "nav-link-selected": {
                "background-color": "#ff4b33",  # Warna tombol aktif
                "color": "white",
            },
        },
    )

# ----------- RENDER HALAMAN -----------
if selected in page_config:
    # Panggil fungsi halaman yang sesuai berdasarkan pilihan sidebar
    page_config[selected]()
else:
    st.error("Halaman tidak ditemukan")
