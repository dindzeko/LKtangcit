import streamlit as st
import pandas as pd
from io import BytesIO

def app():
    st.title("Laporan Realisasi Anggaran (LRA)")

    # Baca file hanya sekali dan simpan di session state
    if "bukubesar" not in st.session_state:
        try:
            st.session_state["bukubesar"] = pd.read_excel(
                "data/bukubesar.xlsb",
                engine="pyxlsb"
            )
        except Exception as e:
            st.error(f"Gagal memuat data bukubesar: {str(e)}")
            return

    if "coa" not in st.session_state:
        try:
            st.session_state["coa"] = pd.read_excel("data/coa.xlsx")
        except Exception as e:
            st.error(f"Gagal memuat data coa: {str(e)}")
            return

    # Ambil DataFrame dari session state
    bukubesar = st.session_state["bukubesar"]
    coa = st.session_state["coa"]

    # Perbaiki parsing kolom tgl_transaksi
    try:
        if "tgl_transaksi" in bukubesar.columns:
            # Jika kolom tgl_transaksi berisi nilai numerik (serial Excel)
            if bukubesar["tgl_transaksi"].dtype in ["float64", "int64"]:
                bukubesar["tgl_transaksi"] = pd.to_datetime(
                    bukubesar["tgl_transaksi"], 
                    unit="D", 
                    origin="1899-12-30"
                )
            else:
                # Parsing tanggal dengan format dd/mm/yyyy
                bukubesar["tgl_transaksi"] = pd.to_datetime(
                    bukubesar["tgl_transaksi"],
                    format="%d/%m/%Y",
                    errors="coerce"
                )
        else:
            st.error("Kolom 'tgl_transaksi' tidak ditemukan dalam file bukubesar.")
            return
    except Exception as e:
        st.error(f"Gagal memproses kolom tgl_transaksi: {str(e)}")
        return

    # Gabungkan bukubesar dengan COA untuk mendapatkan nama akun
    merged_data = pd.merge(
        bukubesar,
        coa[["Kode Akun", "Nama Akun"]],
        left_on="kd_lv_6",
        right_on="Kode Akun",
        how="left"
    )

    # Hitung saldo akun
    merged_data["Saldo"] = merged_data["debet"] - merged_data["kredit"]

    # Filter akun berdasarkan kategori (pendapatan, belanja, pembiayaan)
    akun_pendapatan = merged_data[merged_data["Kode Akun"].astype(str).str.startswith("4")]
    akun_belanja = merged_data[merged_data["Kode Akun"].astype(str).str.startswith("5")]
    akun_pembiayaan = merged_data[merged_data["Kode Akun"].astype(str).str.startswith("6")]

    # Fungsi untuk menghitung saldo berdasarkan hierarki kode
    def hitung_saldo_akun(akun_df, prefix):
        saldo_akun = {}
        
        # Loop melalui semua akun
        for _, row in akun_df.iterrows():
            kode_akun = row["Kode Akun"]
            saldo = row["Saldo"]
            
            # Simpan saldo akun
            saldo_akun[kode_akun] = saldo
            
            # Hitung total untuk setiap level
            for level in range(1, 7):
                parent_code = ".".join(kode_akun.split(".")[:level])
                if parent_code not in saldo_akun:
                    saldo_akun[parent_code] = 0
                saldo_akun[parent_code] += saldo
        
        # Buat DataFrame dari saldo akun
        df_saldo = pd.DataFrame(list(saldo_akun.items()), columns=["Kode Rek", "Saldo"])
        df_saldo["Kode Rek"] = df_saldo["Kode Rek"].astype(str)
        df_saldo["Uraian"] = df_saldo["Kode Rek"].apply(lambda x: f"{prefix} {x}")
        return df_saldo.sort_values(by="Kode Rek")

    # Hitung saldo untuk masing-masing kategori
    saldo_pendapatan = hitung_saldo_akun(akun_pendapatan, "Pendapatan")
    saldo_belanja = hitung_saldo_akun(akun_belanja, "Belanja")
    saldo_pembiayaan = hitung_saldo_akun(akun_pembiayaan, "Pembiayaan")

    # Hitung total pendapatan, belanja, dan surplus/defisit
    total_pendapatan = saldo_pendapatan["Saldo"].sum()
    total_belanja = saldo_belanja["Saldo"].sum()
    surplus_defisit = total_pendapatan - total_belanja

    # Hitung penerimaan dan pengeluaran pembiayaan
    penerimaan_pembiayaan = saldo_pembiayaan[saldo_pembiayaan["Saldo"] > 0]["Saldo"].sum()
    pengeluaran_pembiayaan = saldo_pembiayaan[saldo_pembiayaan["Saldo"] < 0]["Saldo"].sum()
    pembiayaan_netto = penerimaan_pembiayaan + pengeluaran_pembiayaan

    # Hitung SILPA/SIKPA
    silpa_sikpa = surplus_defisit + pembiayaan_netto
    if silpa_sikpa >= 0:
        silpa_sikpa_label = "SILPA"
    else:
        silpa_sikpa_label = "SIKPA"

    # Gabungkan semua komponen laporan
    laporan_lra = pd.concat([saldo_pendapatan, saldo_belanja, saldo_pembiayaan], ignore_index=True)

    # Tambahkan baris total pendapatan, belanja, surplus/defisit, dll.
    laporan_lra = laporan_lra.append({
        "Kode Rek": "",
        "Uraian": "Jumlah Total Pendapatan",
        "Saldo": total_pendapatan
    }, ignore_index=True)

    laporan_lra = laporan_lra.append({
        "Kode Rek": "",
        "Uraian": "Jumlah Total Belanja",
        "Saldo": total_belanja
    }, ignore_index=True)

    laporan_lra = laporan_lra.append({
        "Kode Rek": "",
        "Uraian": "Surplus/Defisit",
        "Saldo": surplus_defisit
    }, ignore_index=True)

    laporan_lra = laporan_lra.append({
        "Kode Rek": "",
        "Uraian": "Penerimaan Pembiayaan",
        "Saldo": penerimaan_pembiayaan
    }, ignore_index=True)

    laporan_lra = laporan_lra.append({
        "Kode Rek": "",
        "Uraian": "Pengeluaran Pembiayaan",
        "Saldo": pengeluaran_pembiayaan
    }, ignore_index=True)

    laporan_lra = laporan_lra.append({
        "Kode Rek": "",
        "Uraian": "Pembiayaan Netto",
        "Saldo": pembiayaan_netto
    }, ignore_index=True)

    laporan_lra = laporan_lra.append({
        "Kode Rek": "",
        "Uraian": f"SILPA / SIKPA ({silpa_sikpa_label})",
        "Saldo": silpa_sikpa
    }, ignore_index=True)

    # Format saldo menjadi Rupiah
    laporan_lra["Saldo"] = laporan_lra["Saldo"].map(lambda x: f"Rp {x:,.0f}")

    # Tampilkan laporan LRA
    st.subheader("Laporan Realisasi Anggaran (LRA)")
    st.dataframe(laporan_lra)

    # Download hasil
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        laporan_lra.to_excel(writer, index=False)
    output.seek(0)
    st.download_button(
        "Unduh Excel",
        data=output,
        file_name="Laporan_LRA.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Jalankan aplikasi
app()
