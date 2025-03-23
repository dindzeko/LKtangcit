import streamlit as st
from streamlit_option_menu import option_menu

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
    """)

# ----------- HALAMAN FILTER DATA -----------
def filter_data_page():
    st.title("Halaman Filter Data")
    st.write("Ini adalah halaman untuk memfilter data transaksi.")

# ----------- HALAMAN LRA -----------
def lra_page():
    st.title("Halaman LRA")
    st.write("Ini adalah halaman untuk Laporan Realisasi Anggaran (LRA).")

# ----------- HALAMAN NERACA -----------
def neraca_page():
    st.title("Halaman Neraca")
    st.write("Ini adalah halaman untuk Laporan Neraca.")

# ----------- HALAMAN LO -----------
def lo_page():
    st.title("Halaman LO")
    st.write("Ini adalah halaman untuk Laporan Operasional (LO).")

# ----------- KONFIGURASI NAVIGASI -----------
page_config = {
    "Main Page": main_page,
    "Filter Data": filter_data_page,
    "LRA": lra_page,
    "Neraca": neraca_page,
    "LO": lo_page,
}

# ----------- SIDEBAR -----------
with st.sidebar:
    selected = option_menu(
        menu_title="Menu Navigasi",  # Judul menu
        options=["Main Page", "Filter Data", "LRA", "Neraca", "LO"],  # Opsi menu
        icons=["house", "funnel", "bar-chart", "clipboard-data", "file-earmark-text"],  # Ikon untuk setiap opsi
        menu_icon="cast",  # Ikon utama untuk menu
        default_index=0,  # Halaman default saat aplikasi dimuat
    )

# ----------- RENDER HALAMAN -----------
if selected in page_config:
    # Panggil fungsi halaman yang sesuai berdasarkan pilihan sidebar
    page_config[selected]()
else:
    st.error("Halaman tidak ditemukan")
