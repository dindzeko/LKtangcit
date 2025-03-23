import pandas as pd
import streamlit as st
from io import BytesIO
import logging

# Konfigurasi logging
logging.basicConfig(level=logging.DEBUG)

def generate_lra():
    st.title("Laporan Realisasi Anggaran (LRA)")
    
    # Validasi session state
    if "bukubesar" not in st.session_state or "coa" not in st.session_state:
        st.error("Data bukubesar atau coa belum dimuat. Pastikan data telah diunggah.")
        return
    
    # Load data dari session state
    bukubesar = st.session_state["bukubesar"]
    coa = st.session_state["coa"]
    
    # Validasi kolom penting
    required_columns_bukubesar = ["kd_lv_6", "debet", "kredit", "jns_transaksi"]
    if not all(col in bukubesar.columns for col in required_columns_bukubesar):
        st.error(f"Kolom berikut harus ada di 'bukubesar': {required_columns_bukubesar}")
        return
    
    required_columns_coa = ["Kode Akun", "Nama Akun", "Level"]
    if not all(col in coa.columns for col in required_columns_coa):
        st.error(f"Kolom berikut harus ada di 'coa': {required_columns_coa}")
        return
    
    # Normalisasi format kode akun
    bukubesar["kd_lv_6"] = bukubesar["kd_lv_6"].astype(str).str.strip()
    coa["Kode Akun"] = coa["Kode Akun"].astype(str).str.strip()
    
    # Filter bukubesar untuk menghilangkan "Jurnal Penutup"
    if "jns_transaksi" in bukubesar.columns:
        bukubesar = bukubesar[bukubesar["jns_transaksi"] != "Jurnal Penutup"]
    else:
        st.error("Kolom 'jns_transaksi' tidak ditemukan di DataFrame 'bukubesar'.")
        return
    
    # Konversi kolom 'debet' dan 'kredit' ke numerik
    bukubesar["debet"] = pd.to_numeric(bukubesar["debet"], errors="coerce").fillna(0)
    bukubesar["kredit"] = pd.to_numeric(bukubesar["kredit"], errors="coerce").fillna(0)
    
    # Fungsi untuk format mata uang
    def format_currency(value):
        return f"Rp {value:,.0f}" if pd.notnull(value) else "Rp 0"
    
    # Membuat struktur LRA
    lra_data = []
    
    # ======================= PENDAPATAN =======================
    # Level 1 Pendapatan
    pendapatan_l1 = coa[(coa["Kode Akun"].str.startswith("4")) & 
                       (coa["Level"] == 1)]
    if not pendapatan_l1.empty:
        total_pendapatan = pendapatan_l1.iloc[0]["Saldo"]  # Ambil saldo level 1
        logging.debug(f"Total Pendapatan (Level 1): {total_pendapatan}")
        lra_data.append({
            "Kode Rek": pendapatan_l1.iloc[0]["Kode Akun"],
            "Uraian": pendapatan_l1.iloc[0]["Nama Akun"],
            "Saldo": total_pendapatan
        })
    else:
        total_pendapatan = 0
        logging.warning("Tidak ada data pendapatan level 1.")
    
    # ======================= BELANJA =======================
    # Level 1 Belanja
    belanja_l1 = coa[(coa["Kode Akun"].str.startswith("5")) & 
                    (coa["Level"] == 1)]
    if not belanja_l1.empty:
        total_belanja = belanja_l1.iloc[0]["Saldo"]  # Ambil saldo level 1
        logging.debug(f"Total Belanja (Level 1): {total_belanja}")
        lra_data.append({
            "Kode Rek": belanja_l1.iloc[0]["Kode Akun"],
            "Uraian": belanja_l1.iloc[0]["Nama Akun"],
            "Saldo": total_belanja
        })
    else:
        total_belanja = 0
        logging.warning("Tidak ada data belanja level 1.")
    
    # ======================= SURPLUS/DEFISIT =======================
    surplus_defisit = total_pendapatan - total_belanja
    logging.debug(f"Surplus/Defisit: {surplus_defisit}")
    lra_data.append({"Kode Rek": "", "Uraian": "Surplus/Defisit", "Saldo": surplus_defisit})
    
    # ======================= PEMBIAYAAN =======================
    # Level 1 Pembiayaan
    pembiayaan_l1 = coa[(coa["Kode Akun"].str.startswith("6")) & 
                       (coa["Level"] == 1)]
    if not pembiayaan_l1.empty:
        total_pembiayaan = pembiayaan_l1.iloc[0]["Saldo"]  # Ambil saldo level 1
        logging.debug(f"Total Pembiayaan (Level 1): {total_pembiayaan}")
        lra_data.append({
            "Kode Rek": pembiayaan_l1.iloc[0]["Kode Akun"],
            "Uraian": pembiayaan_l1.iloc[0]["Nama Akun"],
            "Saldo": total_pembiayaan
        })
    else:
        total_pembiayaan = 0
        logging.warning("Tidak ada data pembiayaan level 1.")
    
    # ======================= SILPA/SIKPA =======================
    silpa_sikpa = surplus_defisit - total_pembiayaan
    logging.debug(f"SILPA/SIKPA: {silpa_sikpa}")
    
    # Tentukan label SILPA atau SIKPA berdasarkan nilai
    if silpa_sikpa < 0:
        uraian_silpa_sikpa = "SILPA"
    else:
        uraian_silpa_sikpa = "SIKPA"
    
    lra_data.append({"Kode Rek": "", "Uraian": uraian_silpa_sikpa, "Saldo": silpa_sikpa})
    
    # Membuat DataFrame hasil
    df_lra = pd.DataFrame(lra_data)
    
    # Formatting output
    df_lra["Saldo"] = df_lra["Saldo"].apply(format_currency)
    
    # Menampilkan tabel
    st.subheader("Laporan Realisasi Anggaran")
    st.table(df_lra[["Kode Rek", "Uraian", "Saldo"]])
    
    # Tombol download
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_lra.to_excel(writer, index=False)
    output.seek(0)
    st.download_button(
        "Unduh LRA",
        data=output,
        file_name="Laporan_Realisasi_Anggaran.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Panggil fungsi generate_lra() di main app
def app():
    # Simulasi memuat data ke session state (sesuaikan dengan cara Anda memuat data)
    # Contoh: st.session_state["bukubesar"] = pd.read_excel("bukubesar.xlsb")
    #         st.session_state["coa"] = pd.read_excel("coa.xlsx")
    if "bukubesar" not in st.session_state or "coa" not in st.session_state:
        st.error("Data belum dimuat. Upload data terlebih dahulu.")
        return
    generate_lra()

if __name__ == "__main__":
    app()
