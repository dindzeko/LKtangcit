import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    try:
        # Baca dan preproses data
        bukubesar = pd.read_excel(
            "data/bukubesar.xlsb", 
            engine="pyxlsb",
            usecols=['kd_lv_6', 'debet', 'kredit', 'tgl_transaksi']
        )
        coa = pd.read_excel("data/coa.xlsx", usecols=['Kode Akun', 'Nama Akun'])
        
        # Konversi tipe data
        bukubesar["kd_lv_6"] = bukubesar["kd_lv_6"].astype(str).str.strip()
        coa["Kode Akun"] = coa["Kode Akun"].astype(str).str.strip()
        
        return bukubesar, coa
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None

def format_currency(value):
    """
    Format angka menjadi format mata uang (Rp).
    Contoh: 1000000 -> "Rp 1.000.000"
    """
    if pd.isna(value) or value == "":
        return "Rp 0"
    
    try:
        # Pastikan nilai adalah numerik
        numeric_value = float(value)
        # Format angka dengan pemisah ribuan
        formatted_value = f"Rp {numeric_value:,.0f}".replace(",", ".")
        return formatted_value
    except ValueError:
        return "Rp 0"
