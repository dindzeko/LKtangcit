import streamlit as st
from streamlit_option_menu import option_menu

# Fungsi untuk menambahkan CSS
def add_css(css):
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# CSS styling (kosongkan dulu untuk fokus perbaikan fungsional)
css_styles = ""
add_css(css_styles)

# Impor modul-modul halaman dari folder `pages/`
try:
    from pages.filterdata import app as filter_data_app
    from pages.lra import app as lra_app
    from pages.neraca import app as neraca_app
    from pages.lo import app as lo_app
    from pages.prosedur_analitis import app as prosedur_analitis_app
except ImportError as e:
    st.error(f"Error importing modules: {str(e)}")
    st.stop()

# Inisialisasi session state
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Main Page"

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
    st.title("Halaman Filter Data")
    filter_data_app()

# ----------- HALAMAN LRA -----------
def lra_page():
    st.title("Halaman LRA")
    lra_app()

# ----------- HALAMAN NERACA -----------
def neraca_page():
    st.title("Halaman Neraca")
    neraca_app()

# ----------- HALAMAN LO -----------
def lo_page():
    st.title("Halaman LO")
    lo_app()

# ----------- HALAMAN PROSEDUR ANALITIS -----------
def prosedur_analitis_page():
    st.title("Halaman Prosedur Analitis")
    prosedur_analitis_app()

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
