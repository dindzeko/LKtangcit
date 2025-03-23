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
