import pandas as pd
import streamlit as st
from io import BytesIO
import logging

# Konfigurasi logging
logging.basicConfig(level=logging.DEBUG)

def calculate_balance(child_code, transaksi):
    """Menghitung saldo berdasarkan jenis akun"""
    if child_code.startswith("4"):
        return transaksi["kredit"].sum() - transaksi["debet"].sum()
    elif child_code.startswith("5"):
        return transaksi["debet"].sum() - transaksi["kredit"].sum()
    elif child_code.startswith("6.1"):
        return transaksi["kredit"].sum() - transaksi["debet"].sum()
    elif child_code.startswith("6.2"):
        return transaksi["debet"].sum() - transaksi["kredit"].sum()
    else:
        return 0

def generate_lra():
    st.title("Laporan Realisasi Anggaran (LRA)")
    
    # Validasi session state
    if "bukubesar" not in st.session_state or "coa" not in st.session_state:
        st.error("Data bukubesar atau coa belum dimuat.")
        return
    
    # Load data
    bukubesar = st.session_state["bukubesar"]
    coa = st.session_state["coa"]
    
    # Validasi kolom
    required_bukubesar = ["kd_lv_6", "debet", "kredit", "jns_transaksi"]
    required_coa = ["Kode Akun", "Nama Akun", "Level"]
    if not all(col in bukubesar.columns for col in required_bukubesar):
        st.error(f"Kolom bukubesar tidak lengkap: {required_bukubesar}")
        return
    if not all(col in coa.columns for col in required_coa):
        st.error(f"Kolom COA tidak lengkap: {required_coa}")
        return
    
    # Filter jurnal penutup
    bukubesar = bukubesar[bukubesar["jns_transaksi"] != "Jurnal Penutup"]
    
    # Konversi ke numerik
    bukubesar["debet"] = pd.to_numeric(bukubesar["debet"], errors="coerce").fillna(0)
    bukubesar["kredit"] = pd.to_numeric(bukubesar["kredit"], errors="coerce").fillna(0)

    # Fungsi rekursif baru dengan penanganan akun khusus
    def calculate_hierarchy(parent_code, current_level, df_coa, df_transaksi):
        children = df_coa[
            df_coa["Kode Akun"].str.startswith(f"{parent_code}.") & 
            (df_coa["Level"] == current_level + 1)
        ]
        
        total = 0
        for _, child in children.iterrows():
            child_code = child["Kode Akun"]
            if child["Level"] == 3:
                transaksi = df_transaksi[df_transaksi["kd_lv_6"] == child_code]
                saldo = calculate_balance(child_code, transaksi)
                logging.debug(f"Saldo {child_code}: {saldo}")
            else:
                saldo = calculate_hierarchy(child_code, child["Level"], df_coa, df_transaksi)
            total += saldo
        return total

    # Membangun struktur LRA
    lra_data = []

    # ======================= PENDAPATAN =======================
    pendapatan_l1 = coa[coa["Kode Akun"].str.startswith("4") & (coa["Level"] == 1)]
    for _, row in pendapatan_l1.iterrows():
        kode = row["Kode Akun"]
        saldo = calculate_hierarchy(kode, 1, coa, bukubesar)
        lra_data.append({
            "Kode Rek": kode,
            "Uraian": row["Nama Akun"],
            "Saldo": saldo
        })
        
        # Level 2
        pendapatan_l2 = coa[coa["Kode Akun"].str.startswith(f"{kode}.") & (coa["Level"] == 2)]
        for _, l2 in pendapatan_l2.iterrows():
            saldo_l2 = calculate_hierarchy(l2["Kode Akun"], 2, coa, bukubesar)
            lra_data.append({
                "Kode Rek": l2["Kode Akun"],
                "Uraian": l2["Nama Akun"],
                "Saldo": saldo_l2
            })
            
            # Level 3
            pendapatan_l3 = coa[
                coa["Kode Akun"].str.startswith(f'{l2["Kode Akun"]}.') & 
                (coa["Level"] == 3)
            ]
            for _, l3 in pendapatan_l3.iterrows():
                transaksi = bukubesar[bukubesar["kd_lv_6"] == l3["Kode Akun"]]
                saldo_l3 = calculate_balance(l3["Kode Akun"], transaksi)
                lra_data.append({
                    "Kode Rek": l3["Kode Akun"],
                    "Uraian": l3["Nama Akun"],
                    "Saldo": saldo_l3
                })

    total_pendapatan = sum(item["Saldo"] for item in lra_data if item["Kode Rek"].startswith("4"))
    lra_data.append({"Kode Rek": "", "Uraian": "Total Pendapatan", "Saldo": total_pendapatan})

    # ======================= BELANJA =======================
    belanja_l1 = coa[coa["Kode Akun"].str.startswith("5") & (coa["Level"] == 1)]
    for _, row in belanja_l1.iterrows():
        kode = row["Kode Akun"]
        saldo = calculate_hierarchy(kode, 1, coa, bukubesar)
        lra_data.append({
            "Kode Rek": kode,
            "Uraian": row["Nama Akun"],
            "Saldo": saldo
        })
        
        # Level 2
        belanja_l2 = coa[coa["Kode Akun"].str.startswith(f"{kode}.") & (coa["Level"] == 2)]
        for _, l2 in belanja_l2.iterrows():
            saldo_l2 = calculate_hierarchy(l2["Kode Akun"], 2, coa, bukubesar)
            lra_data.append({
                "Kode Rek": l2["Kode Akun"],
                "Uraian": l2["Nama Akun"],
                "Saldo": saldo_l2
            })
            
            # Level 3
            belanja_l3 = coa[
                coa["Kode Akun"].str.startswith(f'{l2["Kode Akun"]}.') & 
                (coa["Level"] == 3)
            ]
            for _, l3 in belanja_l3.iterrows():
                transaksi = bukubesar[bukubesar["kd_lv_6"] == l3["Kode Akun"]]
                saldo_l3 = calculate_balance(l3["Kode Akun"], transaksi)
                lra_data.append({
                    "Kode Rek": l3["Kode Akun"],
                    "Uraian": l3["Nama Akun"],
                    "Saldo": saldo_l3
                })

    total_belanja = sum(item["Saldo"] for item in lra_data if item["Kode Rek"].startswith("5"))
    lra_data.append({"Kode Rek": "", "Uraian": "Total Belanja", "Saldo": total_belanja})

    # ======================= SURPLUS/DEFISIT =======================
    surplus_defisit = total_pendapatan - total_belanja
    lra_data.append({"Kode Rek": "", "Uraian": "Surplus/Defisit", "Saldo": surplus_defisit})

    # ======================= PEMBIAYAAN =======================
    pembiayaan_l1 = coa[coa["Kode Akun"].str.startswith("6") & (coa["Level"] == 1)]
    for _, row in pembiayaan_l1.iterrows():
        kode = row["Kode Akun"]
        saldo = calculate_hierarchy(kode, 1, coa, bukubesar)
        lra_data.append({
            "Kode Rek": kode,
            "Uraian": row["Nama Akun"],
            "Saldo": saldo
        })
        
        # Level 2
        pembiayaan_l2 = coa[coa["Kode Akun"].str.startswith(f"{kode}.") & (coa["Level"] == 2)]
        for _, l2 in pembiayaan_l2.iterrows():
            saldo_l2 = calculate_hierarchy(l2["Kode Akun"], 2, coa, bukubesar)
            lra_data.append({
                "Kode Rek": l2["Kode Akun"],
                "Uraian": l2["Nama Akun"],
                "Saldo": saldo_l2
            })
            
            # Level 3
            pembiayaan_l3 = coa[
                coa["Kode Akun"].str.startswith(f'{l2["Kode Akun"]}.') & 
                (coa["Level"] == 3)
            ]
            for _, l3 in pembiayaan_l3.iterrows():
                transaksi = bukubesar[bukubesar["kd_lv_6"] == l3["Kode Akun"]]
                saldo_l3 = calculate_balance(l3["Kode Akun"], transaksi)
                lra_data.append({
                    "Kode Rek": l3["Kode Akun"],
                    "Uraian": l3["Nama Akun"],
                    "Saldo": saldo_l3
                })

    total_pembiayaan = sum(item["Saldo"] for item in lra_data if item["Kode Rek"].startswith("6"))
    lra_data.append({"Kode Rek": "", "Uraian": "Pembiayaan Netto", "Saldo": total_pembiayaan})

    # ======================= SILPA/SIKPA =======================
    silpa = surplus_defisit + total_pembiayaan
    lra_data.append({"Kode Rek": "", "Uraian": "SILPA/SIKPA", "Saldo": silpa})

    # Membuat DataFrame
    df_lra = pd.DataFrame(lra_data)
    
    # Formatting
    def format_currency(value):
        return f"Rp {value:,.0f}" if pd.notnull(value) else "Rp 0"
    
    df_lra["Saldo"] = df_lra["Saldo"].apply(format_currency)
    
    # Tampilkan
    st.subheader("Laporan Realisasi Anggaran")
    st.table(df_lra[["Kode Rek", "Uraian", "Saldo"]])
    
    # Download
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_lra.to_excel(writer, index=False)
    output.seek(0)
    
    st.download_button(
        "Unduh LRA",
        data=output,
        file_name="LRA.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def app():
    if "bukubesar" not in st.session_state or "coa" not in st.session_state:
        st.error("Upload data terlebih dahulu")
        return
    generate_lra()

if __name__ == "__main__":
    app()
