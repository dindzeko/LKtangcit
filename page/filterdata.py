import streamlit as st
import pandas as pd
from io import BytesIO

def app():
    st.title("Halaman Filter Data")

    # Load data
    try:
        # Baca dan proses data COA
        coa = pd.read_excel("data/coa.xlsx")
        
        # Proses split kode akun menjadi level 1-6
        coa_level6 = coa[coa['Level'] == 6].copy()
        coa_level6['kode_split'] = coa_level6['Kode Akun'].apply(lambda x: x.split('.'))
        for i in range(1, 7):
            coa_level6[f'level_{i}'] = coa_level6['kode_split'].apply(
                lambda parts: '.'.join(parts[:i]) if len(parts) >= i else ''
        
        # Baca dan gabung data bukubesar
        bukubesar = pd.read_excel("data/bukubesar.xlsb", engine="pyxlsb")
        merged_data = pd.merge(
            bukubesar,
            coa_level6[['Kode Akun'] + [f'level_{i}' for i in range(1,7)]],
            left_on="kd_lv_6",
            right_on="Kode Akun",
            how="left"
        )
        
        # Konversi ke datetime
        merged_data['tgl_transaksi'] = pd.to_datetime(merged_data['tgl_transaksi'], errors='coerce')
        
    except Exception as e:
        st.error(f"Gagal memuat data: {str(e)}")
        return

    # Widget filtering ---------------------------------------------------------

    # 1. Filter bulan (perbaikan format tanggal)
    st.write("Pilih Bulan:")
    selected_month = st.slider(
        "Bulan Transaksi",
        min_value=1, 
        max_value=12,
        value=(1, 12)
    )
    
    # Filter data
    filtered_data = merged_data[
        (merged_data['tgl_transaksi'].dt.month >= selected_month[0]) & 
        (merged_data['tgl_transaksi'].dt.month <= selected_month[1])
    ]

    # 2. Filter jenis transaksi
    st.write("Pilih Jenis Transaksi:")
    jenis_options = filtered_data['jns_transaksi'].unique().tolist()
    selected_jenis = st.multiselect(
        "Jenis Transaksi",
        options=jenis_options,
        default=jenis_options
    )
    filtered_data = filtered_data[filtered_data['jns_transaksi'].isin(selected_jenis)]

    # 3. Filter unit
    st.write("Pilih Unit:")
    unit_options = ["All"] + filtered_data['nm_unit'].unique().tolist()
    selected_unit = st.radio("Unit", options=unit_options)
    if selected_unit != "All":
        filtered_data = filtered_data[filtered_data['nm_unit'] == selected_unit]

    # 4. Filter level kode (perbaikan nama kolom)
    st.write("Pilih Level Kode Akun:")
    level_options = [1,2,3,4,5,6]
    selected_level = st.selectbox("Level", options=level_options)
    
    if f'level_{selected_level}' in filtered_data.columns:
        level_values = filtered_data[f'level_{selected_level}'].dropna().unique().tolist()
        selected_code = st.selectbox(f"Kode Level {selected_level}", options=level_values)
        filtered_data = filtered_data[filtered_data[f'level_{selected_level}'] == selected_code]
    else:
        st.warning("Data level tidak tersedia")

    # 5. Filter debit/kredit
    st.write("Pilih Tipe Transaksi:")
    dk_type = st.radio("Tipe", options=["All", "Debet", "Kredit"], horizontal=True)
    if dk_type == "Debet":
        filtered_data = filtered_data[filtered_data['debet'] > 0]
    elif dk_type == "Kredit":
        filtered_data = filtered_data[filtered_data['kredit'] > 0]

    # Tampilkan hasil ----------------------------------------------------------
    st.subheader("Hasil Filter")
    top_n = st.number_input("Jumlah Baris", min_value=1, value=20)
    st.dataframe(filtered_data.head(top_n))

    # Download button
    if not filtered_data.empty:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_data.to_excel(writer, index=False)
        st.download_button(
            "Download Excel",
            data=output.getvalue(),
            file_name="filtered_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
