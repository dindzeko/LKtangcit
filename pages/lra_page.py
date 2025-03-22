import pandas as pd
from pyxlsb import open_workbook
import streamlit as st
import io

# Fungsi untuk memuat data
def load_data():
    try:
        # Baca file buku besar (.xlsb)
        with open_workbook("data/bukubesar.xlsb") as wb:
            with wb.get_sheet(1) as sheet:  # Asumsikan data berada di sheet pertama
                buku_besar = pd.DataFrame(sheet.rows())
        
        # Pastikan header benar jika membaca dari .xlsb
        buku_besar.columns = buku_besar.iloc[0]  # Ambil baris pertama sebagai header
        buku_besar = buku_besar[1:]  # Hapus baris header dari data
        
        # Konversi kolom ke tipe data yang sesuai (opsional, jika diperlukan)
        buku_besar = buku_besar.apply(pd.to_numeric, errors='ignore')

        # Baca file COA (.xlsx)
        coa = pd.read_excel("data/coa.xlsx")

        # Bersihkan kolom 'Kode Akun' dari spasi atau karakter tambahan
        coa['Kode Akun'] = coa['Kode Akun'].str.strip()

        return buku_besar, coa
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

# Fungsi untuk mengagregat data ke level 3
def aggregate_to_level3(buku_besar, coa):
    # Gabungkan data dengan COA
    merged = pd.merge(
        buku_besar,
        coa,
        left_on="kd_lv6",
        right_on="Kode Akun",  # Kolom dalam file COA
        how="left"
    )
    
    # Agregat ke level 3
    aggregated = (
        merged.groupby(["kd_lv3", "Nama Akun"])  # Gunakan kolom Nama Akun dari COA
        .agg({"debet": "sum", "kredit": "sum"})
        .reset_index()
    )
    aggregated["saldo"] = aggregated["debet"] - aggregated["kredit"]
    return aggregated

# Fungsi untuk menghitung SILPA
def calculate_silpa(aggregated):
    pendapatan = aggregated.loc[aggregated["kd_lv3"].str.startswith("4"), "saldo"].sum()
    belanja = aggregated.loc[aggregated["kd_lv3"].str.startswith("5"), "saldo"].sum()
    penerimaan_pembiayaan = aggregated.loc[aggregated["kd_lv3"].str.startswith("6.1"), "saldo"].sum()
    pengeluaran_pembiayaan = aggregated.loc[aggregated["kd_lv3"].str.startswith("6.2"), "saldo"].sum()
    silpa = pendapatan - belanja + (penerimaan_pembiayaan - pengeluaran_pembiayaan)
    return silpa

# Fungsi untuk menyusun laporan LRA
def generate_lra_report(aggregated, silpa):
    # Inisialisasi laporan
    lra_report = []

    # Tambahkan header
    lra_report.append(["LRA"])
    lra_report.append(["Indeks Akun", "", "", "", "", "NO", "URAIAN", "", "", "REF", "Debet", "Kredit", "Saldo"])
    lra_report.append(["", "", "", "", "", "1", "", "", "2", "3", "4", "5", "7"])

    # Tambahkan PENDAPATAN
    lra_report.append(["", "", "", "", "", "1", "", "PENDAPATAN", "", "VI.1.1", "", "", ""])
    for _, row in aggregated[aggregated["kd_lv3"].str.startswith("4")].iterrows():
        lra_report.append([
            row["kd_lv3"],
            "",
            "",
            "",
            "",
            "",
            "",
            row["Nama Akun"],  # Gunakan Nama Akun dari COA
            "",
            "",
            row["debet"],
            row["kredit"],
            row["saldo"]
        ])

    # Tambahkan BELANJA
    lra_report.append(["", "", "", "", "", "2", "", "BELANJA", "", "VI.1.2", "", "", ""])
    for _, row in aggregated[aggregated["kd_lv3"].str.startswith("5")].iterrows():
        lra_report.append([
            row["kd_lv3"],
            "",
            "",
            "",
            "",
            "",
            "",
            row["Nama Akun"],  # Gunakan Nama Akun dari COA
            "",
            "",
            row["debet"],
            row["kredit"],
            row["saldo"]
        ])

    # Tambahkan PEMBIAYAAN
    lra_report.append(["", "", "", "", "", "4", "", "PEMBIAYAAN", "", "VI.1.5", "", "", ""])
    for _, row in aggregated[aggregated["kd_lv3"].str.startswith("6")].iterrows():
        lra_report.append([
            row["kd_lv3"],
            "",
            "",
            "",
            "",
            "",
            "",
            row["Nama Akun"],  # Gunakan Nama Akun dari COA
            "",
            "",
            row["debet"],
            row["kredit"],
            row["saldo"]
        ])

    # Tambahkan SILPA
    lra_report.append(["", "", "", "", "", "4.3", "", "SISA LEBIH PEMBIAYAAN ANGGARAN (SILPA)", "", "VI.1.6", "", "", silpa])

    return lra_report

# Main function untuk Streamlit
def main():
    st.title("Laporan Realisasi Anggaran (LRA)")

    # Load data
    buku_besar, coa = load_data()
    if buku_besar is None or coa is None:
        return

    # Aggregate data to level 3
    aggregated = aggregate_to_level3(buku_besar, coa)

    # Calculate SILPA
    silpa = calculate_silpa(aggregated)

    # Generate LRA report
    lra_report = generate_lra_report(aggregated, silpa)

    # Convert to DataFrame
    df_lra = pd.DataFrame(lra_report)

    # Tampilkan laporan LRA
    st.subheader("Laporan Realisasi Anggaran")
    st.write("Berikut adalah laporan LRA yang telah dihasilkan:")
    st.dataframe(df_lra)

    # Opsi untuk mengunduh laporan sebagai file Excel
    def convert_df_to_excel(df):
        """Konversi DataFrame ke file Excel."""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, header=False)
        output.seek(0)
        return output

    excel_file = convert_df_to_excel(df_lra)
    st.download_button(
        label="Download Laporan LRA sebagai Excel",
        data=excel_file,
        file_name="LRA_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    main()
