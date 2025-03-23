import pandas as pd
import streamlit as st
from io import BytesIO

# Konfigurasi logging
import logging
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
    bukubesar["kd_lv_6"] = bukubesar["kd_lv_6"].str.strip()
    coa["Kode Akun"] = coa["Kode Akun"].str.strip()
    
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
    
    # Fungsi rekursif untuk menghitung saldo hierarki
    def calculate_hierarchy(parent_code, level, df_coa, df_transaksi):
        children = df_coa[df_coa["Kode Akun"].str.startswith(parent_code + ".") & 
                         (df_coa["Level"] == level + 1)]
        total = 0
        for _, child in children.iterrows():
            child_code = child["Kode Akun"]
            if child["Level"] == 3:  # Level terendah (detail transaksi)
                parent_code = ".".join(child_code.split(".")[:3])  # Ambil level 3
                transaksi = df_transaksi[df_transaksi["kd_lv_6"].str.startswith(parent_code)]
                saldo = transaksi["debet"].sum() - transaksi["kredit"].sum()
                logging.debug(f"Saldo untuk akun {child_code}: {saldo}")
            else:  # Rekursif untuk level di atasnya
                saldo = calculate_hierarchy(child_code, child["Level"], df_coa, df_transaksi)
            total += saldo
        return total
    
    # Membuat struktur LRA
    lra_data = []
    
    # ======================= PENDAPATAN =======================
    pendapatan_l1 = coa[(coa["Kode Akun"].str.startswith("4")) & (coa["Level"] == 1)]
    for _, row in pendapatan_l1.iterrows():
        kode = row["Kode Akun"]
        saldo = calculate_hierarchy(kode, 1, coa, bukubesar)
        logging.debug(f"Pendapatan Level 1 - Kode: {kode}, Saldo: {saldo}")
        lra_data.append({
            "Kode Rek": kode,
            "Uraian": row["Nama Akun"],
            "Saldo": saldo
        })
        
        # Level 2
        pendapatan_l2 = coa[(coa["Kode Akun"].str.startswith(f"{kode}.")) & (coa["Level"] == 2)]
        for _, l2 in pendapatan_l2.iterrows():
            saldo_l2 = calculate_hierarchy(l2["Kode Akun"], 2, coa, bukubesar)
            logging.debug(f"Pendapatan Level 2 - Kode: {l2['Kode Akun']}, Saldo: {saldo_l2}")
            lra_data.append({
                "Kode Rek": l2["Kode Akun"],
                "Uraian": l2["Nama Akun"],
                "Saldo": saldo_l2
            })
            
            # Level 3
            pendapatan_l3 = coa[(coa["Kode Akun"].str.startswith(f'{l2["Kode Akun"]}.')) & (coa["Level"] == 3)]
            for _, l3 in pendapatan_l3.iterrows():
                parent_code = ".".join(l3["Kode Akun"].split(".")[:3])  # Ambil level 3
                transaksi = bukubesar[bukubesar["kd_lv_6"].str.startswith(parent_code)]
                saldo_l3 = transaksi["debet"].sum() - transaksi["kredit"].sum()
                logging.debug(f"Pendapatan Level 3 - Kode: {l3['Kode Akun']}, Saldo: {saldo_l3}")
                lra_data.append({
                    "Kode Rek": l3["Kode Akun"],
                    "Uraian": l3["Nama Akun"],
                    "Saldo": saldo_l3
                })
    
    # Total Pendapatan
    total_pendapatan = sum(item["Saldo"] for item in lra_data if item["Kode Rek"].startswith("4"))
    logging.debug(f"Total Pendapatan: {total_pendapatan}")
    lra_data.append({"Kode Rek": "", "Uraian": "Jumlah total pendapatan", "Saldo": total_pendapatan})
    
    # ======================= BELANJA =======================
    belanja_l1 = coa[(coa["Kode Akun"].str.startswith("5")) & (coa["Level"] == 1)]
    for _, row in belanja_l1.iterrows():
        kode = row["Kode Akun"]
        saldo = calculate_hierarchy(kode, 1, coa, bukubesar)
        logging.debug(f"Belanja Level 1 - Kode: {kode}, Saldo: {saldo}")
        lra_data.append({
            "Kode Rek": kode,
            "Uraian": row["Nama Akun"],
            "Saldo": saldo
        })
        
        # Level 2
        belanja_l2 = coa[(coa["Kode Akun"].str.startswith(f"{kode}.")) & (coa["Level"] == 2)]
        for _, l2 in belanja_l2.iterrows():
            saldo_l2 = calculate_hierarchy(l2["Kode Akun"], 2, coa, bukubesar)
            logging.debug(f"Belanja Level 2 - Kode: {l2['Kode Akun']}, Saldo: {saldo_l2}")
            lra_data.append({
                "Kode Rek": l2["Kode Akun"],
                "Uraian": l2["Nama Akun"],
                "Saldo": saldo_l2
            })
            
            # Level 3
            belanja_l3 = coa[(coa["Kode Akun"].str.startswith(f'{l2["Kode Akun"]}.')) & (coa["Level"] == 3)]
            for _, l3 in belanja_l3.iterrows():
                parent_code = ".".join(l3["Kode Akun"].split(".")[:3])  # Ambil level 3
                transaksi = bukubesar[bukubesar["kd_lv_6"].str.startswith(parent_code)]
                saldo_l3 = transaksi["debet"].sum() - transaksi["kredit"].sum()
                logging.debug(f"Belanja Level 3 - Kode: {l3['Kode Akun']}, Saldo: {saldo_l3}")
                lra_data.append({
                    "Kode Rek": l3["Kode Akun"],
                    "Uraian": l3["Nama Akun"],
                    "Saldo": saldo_l3
                })
    
    # Total Belanja
    total_belanja = sum(item["Saldo"] for item in lra_data if item["Kode Rek"].startswith("5"))
    logging.debug(f"Total Belanja: {total_belanja}")
    lra_data.append({"Kode Rek": "", "Uraian": "Jumlah total belanja", "Saldo": total_belanja})
    
    # ======================= SURPLUS/DEFISIT =======================
    surplus_defisit = total_pendapatan - total_belanja
    logging.debug(f"Surplus/Defisit: {surplus_defisit}")
    lra_data.append({"Kode Rek": "", "Uraian": "Surplus/Defisit", "Saldo": surplus_defisit})
    
    # ======================= PEMBIAYAAN =======================
    pembiayaan_l1 = coa[(coa["Kode Akun"].str.startswith("6")) & (coa["Level"] == 1)]
    for _, row in pembiayaan_l1.iterrows():
        kode = row["Kode Akun"]
        saldo = calculate_hierarchy(kode, 1, coa, bukubesar)
        logging.debug(f"Pembiayaan Level 1 - Kode: {kode}, Saldo: {saldo}")
        lra_data.append({
            "Kode Rek": kode,
            "Uraian": row["Nama Akun"],
            "Saldo": saldo
        })
        
        # Level 2
        pembiayaan_l2 = coa[(coa["Kode Akun"].str.startswith(f"{kode}.")) & (coa["Level"] == 2)]
        for _, l2 in pembiayaan_l2.iterrows():
            saldo_l2 = calculate_hierarchy(l2["Kode Akun"], 2, coa, bukubesar)
            logging.debug(f"Pembiayaan Level 2 - Kode: {l2['Kode Akun']}, Saldo: {saldo_l2}")
            lra_data.append({
                "Kode Rek": l2["Kode Akun"],
                "Uraian": l2["Nama Akun"],
                "Saldo": saldo_l2
            })
            
            # Level 3
            pembiayaan_l3 = coa[(coa["Kode Akun"].str.startswith(f'{l2["Kode Akun"]}.')) & (coa["Level"] == 3)]
            for _, l3 in pembiayaan_l3.iterrows():
                parent_code = ".".join(l3["Kode Akun"].split(".")[:3])  # Ambil level 3
                transaksi = bukubesar[bukubesar["kd_lv_6"].str.startswith(parent_code)]
                saldo_l3 = transaksi["debet"].sum() - transaksi["kredit"].sum()
                logging.debug(f"Pembiayaan Level 3 - Kode: {l3['Kode Akun']}, Saldo: {saldo_l3}")
                lra_data.append({
                    "Kode Rek": l3["Kode Akun"],
                    "Uraian": l3["Nama Akun"],
                    "Saldo": saldo_l3
                })
    
    # Total Pembiayaan
    total_pembiayaan_penerimaan = sum(item["Saldo"] for item in lra_data if item["Kode Rek"].startswith("6.1"))
    total_pembiayaan_pengeluaran = sum(item["Saldo"] for item in lra_data if item["Kode Rek"].startswith("6.2"))
    pembiayaan_netto = total_pembiayaan_penerimaan - total_pembiayaan_pengeluaran
    logging.debug(f"Pembiayaan Netto: {pembiayaan_netto}")
    lra_data.append({"Kode Rek": "", "Uraian": "Pembiayaan Netto", "Saldo": pembiayaan_netto})
    
    # ======================= SILPA/SIKPA =======================
    silpa = surplus_defisit + pembiayaan_netto
    logging.debug(f"SILPA/SIKPA: {silpa}")
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
