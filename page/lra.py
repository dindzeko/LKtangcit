import pandas as pd
import streamlit as st
from io import BytesIO

def generate_lra():
    st.title("Laporan Realisasi Anggaran (LRA)")
    
    # Load data dari session state
    bukubesar = st.session_state["bukubesar"]
    coa = st.session_state["coa"]
    
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
            if child["Level"] == 3:  # Ambil saldo langsung dari transaksi
                transaksi = df_transaksi[df_transaksi["kd_lv_6"] == child_code]
                saldo = transaksi["debet"].sum() - transaksi["kredit"].sum()
            else:  # Rekursif untuk level di atasnya
                saldo = calculate_hierarchy(child_code, child["Level"], df_coa, df_transaksi)
            
            total += saldo
        return total

    # Membuat struktur LRA
    lra_data = []

    # ======================= PENDAPATAN =======================
    # Level 1 Pendapatan
    pendapatan_l1 = coa[(coa["Kode Akun"].str.startswith("4")) & 
                       (coa["Level"] == 1)]
    
    for _, row in pendapatan_l1.iterrows():
        kode = row["Kode Akun"]
        saldo = calculate_hierarchy(kode, 1, coa, bukubesar)
        lra_data.append({
            "Kode Rek": kode,
            "Uraian": row["Nama Akun"],
            "Saldo": saldo
        })
        
        # Level 2
        pendapatan_l2 = coa[(coa["Kode Akun"].str.startswith(f"{kode}.")) & 
                           (coa["Level"] == 2)]
        for _, l2 in pendapatan_l2.iterrows():
            saldo_l2 = calculate_hierarchy(l2["Kode Akun"], 2, coa, bukubesar)
            lra_data.append({
                "Kode Rek": l2["Kode Akun"],
                "Uraian": l2["Nama Akun"],
                "Saldo": saldo_l2
            })
            
            # Level 3
            pendapatan_l3 = coa[(coa["Kode Akun"].str.startswith(f"{l2["Kode Akun"]}.")) & 
                              (coa["Level"] == 3)]
            for _, l3 in pendapatan_l3.iterrows():
                transaksi = bukubesar[bukubesar["kd_lv_6"] == l3["Kode Akun"]]
                saldo_l3 = transaksi["debet"].sum() - transaksi["kredit"].sum()
                lra_data.append({
                    "Kode Rek": l3["Kode Akun"],
                    "Uraian": l3["Nama Akun"],
                    "Saldo": saldo_l3
                })

    # Total Pendapatan
    total_pendapatan = sum(item["Saldo"] for item in lra_data if item["Kode Rek"].startswith("4"))
    lra_data.append({"Kode Rek": "", "Uraian": "Jumlah total pendapatan", "Saldo": total_pendapatan})

    # ======================= BELANJA =======================
    # Proses serupa untuk belanja (kode 5.x)
    # ... (implementasi mirip dengan bagian pendapatan)

    # ======================= SURPLUS/DEFISIT =======================
    total_belanja = 0  # Diisi dari hasil belanja
    surplus_defisit = total_pendapatan - total_belanja
    lra_data.append({"Kode Rek": "", "Uraian": "Surplus/Defisit", "Saldo": surplus_defisit})

    # ======================= PEMBIAYAAN =======================
    # Proses untuk pembiayaan (kode 6.x)
    # ... (implementasi mirip dengan bagian pendapatan)

    # ======================= SILPA/SIKPA =======================
    pembiayaan_netto = 0  # Diisi dari hasil pembiayaan
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

# Panggil fungsi generate_lra() di main app
def app():
    # Kode inisialisasi data sama seperti sebelumnya
    # ...
    generate_lra()

if __name__ == "__main__":
    app()
