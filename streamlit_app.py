import streamlit as st
from streamlit_option_menu import option_menu

# Impor modul-modul
try:
    from modules.filter_data import app as filter_data_app
    from modules.lra import app as lra_app
    from modules.neraca import app as neraca_app
    from modules.lo import app as lo_app
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
    """)

# ----------- KONFIGURASI NAVIGASI -----------
page_config = {
    "Main Page": main_page,
    "Filter Data": filter_data_app,
    "LRA": lra_app,
    "Neraca": neraca_app,
    "LO": lo_app,
}

# ----------- SIDEBAR -----------
with st.sidebar:
    selected = option_menu(
        menu_title="Menu",
        options=list(page_config.keys()),
        icons=["house", "funnel", "bar-chart", "clipboard-data", "file-earmark-text"],
        menu_icon="cast",
        default_index=0,
    )

# ----------- RENDER HALAMAN -----------
if selected in page_config:
    if selected == "Main Page":
        page_config[selected]()  # Panggil fungsi langsung untuk halaman utama
    else:
        st.session_state["current_page"] = selected
        page_config[selected]()  # Panggil fungsi untuk halaman lainnya
else:
    st.error("Halaman tidak ditemukan")
