import pandas as pd

@st.cache_data
def load_data():
    """Muat dan cache data untuk optimasi"""
    try:
        # Baca dan preproses data
        bukubesar = pd.read_excel("data/bukubesar.xlsb", engine="pyxlsb")
        coa = pd.read_excel("data/coa.xlsx")
        
        # Konversi tipe data
        bukubesar["kd_lv_6"] = bukubesar["kd_lv_6"].astype(str)
        coa["Kode Akun"] = coa["Kode Akun"].astype(str)
        
        # Parsing tanggal dengan vectorized operation
        bukubesar["tgl_transaksi"] = pd.to_datetime(
            bukubesar["tgl_transaksi"], 
            errors="coerce",
            format="mixed"
        )
        
        return bukubesar, coa
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None
