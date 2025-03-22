import streamlit as st

# Judul Aplikasi
st.set_page_config(page_title="Laporan Keuangan", layout="wide")

# Sidebar untuk navigasi
st.sidebar.title("Menu")
page = st.sidebar.selectbox(
    "Pilih Halaman",
    ["Filter Data", "LRA", "Neraca", "LO"],
)

# Routing ke halaman lain
if page == "Filter Data":
    from pages.filter_page import show_filter_page
    show_filter_page()

elif page == "LRA":
    from pages.lra_page import show_lra_page
    show_lra_page()

elif page == "Neraca":
    from pages.neraca_page import show_neraca_page
    show_neraca_page()

elif page == "LO":
    from pages.lo_page import show_lo_page
    show_lo_page()
