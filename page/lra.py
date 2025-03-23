import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# Impor fungsi load_data dari utils.py
from utils import load_data

def hitung_saldo_cepat(_df, kode_col, saldo_col):
    """Fungsi teroptimasi untuk menghitung saldo hierarki"""
    # Split kode akun menjadi komponen
    split_codes = _df[kode_col].str.split('.', expand=True)
    
    # Generate semua parent code
    parent_codes = []
    for level in range(1, 7):
        level_codes = split_codes.iloc[:, :level].agg('.'.join, axis=1)
        parent_codes.append(level_codes)
    
    # Gabungkan dengan saldo
    exploded = pd.concat([
        pd.DataFrame({'Kode Rek': code, 'Saldo': _df[saldo_col]})
        for code in parent_codes
    ])
    
    # Group dan aggregasi
    return exploded.groupby('Kode Rek', as_index=False)['Saldo'].sum()

def buat_laporan():
    # Muat data menggunakan fungsi dari utils.py
    bukubesar, coa = load_data()
    if bukubesar is None or coa is None:
        return
    
    # Gabungkan data dengan merge cepat
    merged = pd.merge(
        bukubesar,
        coa[["Kode Akun", "Nama Akun"]],
        left_on="kd_lv_6",
        right_on="Kode Akun",
        how="left"
    )
    
    # Hitung saldo dengan vectorized operation
    merged["Saldo"] = merged["debet"] - merged["kredit"]
    
    # Filter dengan boolean indexing
    mask_pendapatan = merged["Kode Akun"].str.startswith("4", na=False)
    mask_belanja = merged["Kode Akun"].str.startswith("5", na=False)
    mask_pembiayaan = merged["Kode Akun"].str.startswith("6", na=False)
    
    # Hitung saldo hierarki dengan fungsi cepat
    saldo_pendapatan = hitung_saldo_cepat(merged[mask_pendapatan], "Kode Akun", "Saldo")
    saldo_belanja = hitung_saldo_cepat(merged[mask_belanja], "Kode Akun", "Saldo")
    saldo_pembiayaan = hitung_saldo_cepat(merged[mask_pembiayaan], "Kode Akun", "Saldo")
    
    # Gabungkan hasil
    laporan = pd.concat([
        saldo_pendapatan.assign(Uraian="Pendapatan " + saldo_pendapatan["Kode Rek"]),
        saldo_belanja.assign(Uraian="Belanja " + saldo_belanja["Kode Rek"]),
        saldo_pembiayaan.assign(Uraian="Pembiayaan " + saldo_pembiayaan["Kode Rek"])
    ])
    
    # Hitung total dengan numpy untuk performa
    totals = [
        ("Jumlah Total Pendapatan", saldo_pendapatan["Saldo"].sum()),
        ("Jumlah Total Belanja", saldo_belanja["Saldo"].sum()),
        ("Surplus/Defisit", saldo_pendapatan["Saldo"].sum() - saldo_belanja["Saldo"].sum())
    ]
    
    # Tambahkan total ke dataframe
    total_df = pd.DataFrame([{
        "Kode Rek": "",
        "Uraian": label,
        "Saldo": np.sum(value)
    } for label, value in totals])
    
    laporan = pd.concat([laporan, total_df], ignore_index=True)
    
    # Format mata uang
    laporan["Saldo"] = laporan["Saldo"].map(lambda x: f"Rp {x:,.0f}")
    
    # Tampilkan hasil
    st.subheader("Laporan Realisasi Anggaran (LRA)")
    st.dataframe(laporan)
    
    # Download
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        laporan.to_excel(writer, index=False)
    output.seek(0)
    st.download_button("Unduh Laporan", output.getvalue(), file_name="LRA.xlsx")

def app():
    st.title("Laporan Realisasi Anggaran (LRA) - Optimized")
    buat_laporan()

if __name__ == "__main__":
    app()
