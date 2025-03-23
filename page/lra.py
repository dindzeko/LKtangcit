import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from utils import load_data

def hitung_saldo_cepat(df, kode_col, saldo_col):
    """Fungsi teroptimasi untuk menghitung saldo hierarki dengan vectorized operations"""
    try:
        # Split kode akun dan explode untuk semua level
        split_df = df[kode_col].str.split('.', expand=True)
        max_level = min(6, split_df.shape[1])  # Pastikan tidak melebihi kolom yang ada
        
        exploded = pd.concat([
            df.assign(
                Level=level,
                Parent=split_df.iloc[:, :level].agg('.'.join, axis=1)
            )
            for level in range(1, max_level+1)
        ])
        
        # Gabungkan dengan kode asli
        full_hierarchy = pd.concat([
            exploded[['Parent', saldo_col]].rename(columns={'Parent': 'Kode Rek'}),
            df[[kode_col, saldo_col]].rename(columns={kode_col: 'Kode Rek'})
        ])
        
        return full_hierarchy.groupby('Kode Rek', as_index=False)[saldo_col].sum()
    
    except Exception as e:
        st.error(f"Error dalam perhitungan hierarki: {str(e)}")
        return pd.DataFrame()

def format_currency(value):
    """Format numerik ke Rupiah dengan handling NaN"""
    if pd.isna(value):
        return "Rp 0"
    return f"Rp {value:,.0f}".replace(",", ".")

def buat_laporan():
    try:
        # Muat data dengan progress bar
        with st.spinner('Memuat data...'):
            bukubesar, coa = load_data()
            if bukubesar is None or coa is None:
                return

        # Validasi kolom penting
        required_cols = {'kd_lv_6', 'debet', 'kredit'}
        if not required_cols.issubset(bukubesar.columns):
            st.error("Kolom wajib tidak ditemukan dalam data bukubesar")
            return

        # Merge data dengan optimasi memori
        with st.spinner('Menggabungkan data...'):
            merged = pd.merge(
                bukubesar[['kd_lv_6', 'debet', 'kredit']],
                coa[["Kode Akun", "Nama Akun"]],
                left_on="kd_lv_6",
                right_on="Kode Akun",
                how="left"
            )
            merged["Saldo"] = merged["debet"] - merged["kredit"]

        # Filter data dengan boolean indexing
        with st.spinner('Memproses data...'):
            mask_pendapatan = merged["Kode Akun"].str.startswith("4", na=False)
            mask_belanja = merged["Kode Akun"].str.startswith("5", na=False)
            mask_pembiayaan = merged["Kode Akun"].str.startswith("6", na=False)

            # Hitung saldo paralel dengan cache
            @st.cache_data
            def proses_kategori(_mask, label):
                return hitung_saldo_cepat(merged[_mask], "Kode Akun", "Saldo").assign(Uraian=label)

            saldo_pendapatan = proses_kategori(mask_pendapatan, "Pendapatan ")
            saldo_belanja = proses_kategori(mask_belanja, "Belanja ")
            saldo_pembiayaan = proses_kategori(mask_pembiayaan, "Pembiayaan ")

        # Gabungkan hasil
        with st.spinner('Menyusun laporan...'):
            laporan = pd.concat([
                saldo_pendapatan,
                saldo_belanja,
                saldo_pembiayaan
            ], ignore_index=True)

            # Hitung total dengan numpy
            totals = [
                ("Jumlah Total Pendapatan", saldo_pendapatan["Saldo"].sum()),
                ("Jumlah Total Belanja", saldo_belanja["Saldo"].sum()),
                ("Surplus/Defisit", saldo_pendapatan["Saldo"].sum() - saldo_belanja["Saldo"].sum())
            ]
            
            # Tambahkan total
            total_df = pd.DataFrame([{
                "Kode Rek": "",
                "Uraian": label,
                "Saldo": value
            } for label, value in totals])
            
            laporan = pd.concat([laporan, total_df], ignore_index=True)

            # Format mata uang
            laporan["Saldo"] = laporan["Saldo"].apply(format_currency)

        # Tampilkan hasil
        st.subheader("Laporan Realisasi Anggaran (LRA)")
        st.dataframe(laporan, use_container_width=True)

        # Download
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            laporan.to_excel(writer, index=False)
        output.seek(0)
        
        st.download_button(
            "📥 Unduh Laporan",
            output.getvalue(),
            file_name="LRA.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Terjadi kesalahan sistem: {str(e)}")
        st.stop()

def app():
    st.title("Laporan Realisasi Anggaran (LRA) - Optimized")
    buat_laporan()

if __name__ == "__main__":
    app()
