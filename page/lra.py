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
    bukubesar = st.session_state["bukubesar"].copy()
    coa = st.session_state["coa"].copy()
    
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
    bukubesar["kd_lv_6"] = bukubesar["kd_lv_6"].str.strip()
    coa["Kode Akun"] = coa["Kode Akun"].str.strip()
    
    # Filter bukubesar untuk menghilangkan "Jurnal Penutup"
    bukubesar = bukubesar[bukubesar["jns_transaksi"] != "Jurnal Penutup"]
    
    # Konversi kolom 'debet' dan 'kredit' ke numerik
    bukubesar["debet"] = pd.to_numeric(bukubesar["debet"], errors="coerce").fillna(0)
    bukubesar["kredit"] = pd.to_numeric(bukubesar["kredit"], errors="coerce").fillna(0)
    
    # Fungsi untuk format mata uang
    def format_currency(value):
        return f"Rp {value:,.0f}" if pd.notnull(value) else "Rp 0"

    # Fungsi untuk mencari parent Level 3
    coa_level3 = coa[coa["Level"] == 3]
    coa_level3_codes = set(coa_level3["Kode Akun"].unique())
    
    def find_parent_level3(kode):
        parts = kode.split('.')
        for i in range(len(parts), 0, -1):
            candidate = '.'.join(parts[:i])
            if candidate in coa_level3_codes:
                return candidate
        return None
    
    # Mapping transaksi ke Level 3
    bukubesar["level3_code"] = bukubesar["kd_lv_6"].apply(find_parent_level3)
    bukubesar = bukubesar.dropna(subset=["level3_code"])
    
    # Hitung saldo per Level 3
    aggregated = bukubesar.groupby("level3_code").agg({
        "debet": "sum",
        "kredit": "sum"
    }).reset_index()
    
    level3_balances = {}
    for _, row in aggregated.iterrows():
        level3_code = row["level3_code"]
        saldo = row["debet"] - row["kredit"]
        level3_balances[level3_code] = saldo
    
    # Precompute balances untuk semua level
    balances = {}
    
    # Isi saldo Level 3
    for code in coa_level3["Kode Akun"]:
        balances[code] = level3_balances.get(code, 0)
    
    # Hitung saldo Level 2
    coa_level2 = coa[coa["Level"] == 2]
    for _, row in coa_level2.iterrows():
        kode = row["Kode Akun"]
        children = coa[(coa["Kode Akun"].str.startswith(f"{kode}.")) & (coa["Level"] == 3)]
        saldo = sum(balances.get(child, 0) for child in children["Kode Akun"])
        balances[kode] = saldo
    
    # Hitung saldo Level 1
    coa_level1 = coa[coa["Level"] == 1]
    for _, row in coa_level1.iterrows():
        kode = row["Kode Akun"]
        children = coa[(coa["Kode Akun"].str.startswith(f"{kode}.")) & (coa["Level"] == 2)]
        saldo = sum(balances.get(child, 0) for child in children["Kode Akun"])
        balances[kode] = saldo
    
    # Fungsi untuk generate laporan hierarki
    def generate_report(kode_start, level, df_coa):
        report_data = []
        parent = df_coa[df_coa["Kode Akun"] == kode_start].iloc[0]
        report_data.append({
            "Kode Rek": parent["Kode Akun"],
            "Uraian": parent["Nama Akun"],
            "Saldo": balances.get(parent["Kode Akun"], 0)
        })
        
        children = df_coa[df_coa["Kode Akun"].str.startswith(f"{kode_start}."))]
        for _, child in children.iterrows():
            if child["Level"] == level + 1:
                report_data.append({
                    "Kode Rek": child["Kode Akun"],
                    "Uraian": child["Nama Akun"],
                    "Saldo": balances.get(child["Kode Akun"], 0)
                })
                if child["Level"] < 3:
                    report_data += generate_report(child["Kode Akun"], child["Level"], df_coa)
        return report_data
    
    # Membuat struktur LRA
    lra_data = []
    
    # ======================= PENDAPATAN =======================
    pendapatan_l1 = coa[(coa["Kode Akun"].str.startswith("4")) & (coa["Level"] == 1)]
    for _, row in pendapatan_l1.iterrows():
        lra_data += generate_report(row["Kode Akun"], 1, coa)
    
    # Total Pendapatan
    total_pendapatan = sum(balances[kode] for kode in pendapatan_l1["Kode Akun"])
    lra_data.append({"Kode Rek": "", "Uraian": "Jumlah total pendapatan", "Saldo": total_pendapatan})
    
    # ======================= BELANJA =======================
    belanja_l1 = coa[(coa["Kode Akun"].str.startswith("5")) & (coa["Level"] == 1)]
    for _, row in belanja_l1.iterrows():
        lra_data += generate_report(row["Kode Akun"], 1, coa)
    
    # Total Belanja
    total_belanja = sum(balances[kode] for kode in belanja_l1["Kode Akun"])
    lra_data.append({"Kode Rek": "", "Uraian": "Jumlah total belanja", "Saldo": total_belanja})
    
    # ======================= SURPLUS/DEFISIT =======================
    surplus_defisit = total_pendapatan - total_belanja
    lra_data.append({"Kode Rek": "", "Uraian": "Surplus/Defisit", "Saldo": surplus_defisit})
    
    # ======================= PEMBIAYAAN =======================
    pembiayaan_l1 = coa[(coa["Kode Akun"].str.startswith("6")) & (coa["Level"] == 1)]
    for _, row in pembiayaan_l1.iterrows():
        lra_data += generate_report(row["Kode Akun"], 1, coa)
    
    # Total Pembiayaan
    penerimaan = sum(balances[kode] for kode in coa[coa["Kode Akun"].str.startswith("6.1")]["Kode Akun"])
    pengeluaran = sum(balances[kode] for kode in coa[coa["Kode Akun"].str.startswith("6.2")]["Kode Akun"])
    pembiayaan_netto = penerimaan - pengeluaran
    lra_data.append({"Kode Rek": "", "Uraian": "Pembiayaan Netto", "Saldo": pembiayaan_netto})
    
    # ======================= SILPA/SIKPA =======================
    silpa = surplus_defisit + pembiayaan_netto
    lra_data.append({"Kode Rek": "", "Uraian": "SILPA/SIKPA", "Saldo": silpa})
    
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

def app():
    if "bukubesar" not in st.session_state or "coa" not in st.session_state:
        st.error("Data belum dimuat. Upload data terlebih dahulu.")
        return
    
    generate_lra()

if __name__ == "__main__":
    app()
