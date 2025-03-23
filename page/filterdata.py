import streamlit as st
import pandas as pd
from io import BytesIO
from utils import load_data, format_currency  # Anggap utils.py sudah ada

def validate_input(filtered_data):
    """Validasi apakah data hasil filter kosong"""
    if filtered_data.empty:
        st.warning("Tidak ada data yang sesuai dengan filter.")
        return False
    return True

def apply_filters(bukubesar, coa, selected_month, selected_jns, selected_unit, kode_akun):
    """Terapkan filter ke data bukubesar"""
    # Filter dasar
    filtered = bukubesar[
        (bukubesar['tgl_transaksi'].dt.month.between(*selected_month)) &
        (bukubesar['jns_transaksi'].isin(selected_jns))
    ]
    
    # Filter unit
    if selected_unit != "Semua":
        filtered = filtered[filtered['nm_unit'] == selected_unit]
    
    # Filter hierarki akun
    filtered = filtered[filtered['kd_lv_6'].str.startswith(kode_akun)]
    
    return filtered

def display_results(filtered_data, coa):
    """Tampilkan hasil filter dan tambahkan opsi unduh"""
    # Gabungkan dengan data COA
    merged = pd.merge(
        filtered_data,
        coa[['Kode Akun', 'Nama Akun']],
        left_on='kd_lv_6',
        right_on='Kode Akun',
        how='left'
    )
    
    # Format output
    merged['debet'] = merged['debet'].apply(format_currency)
    merged['kredit'] = merged['kredit'].apply(format_currency)
    
    # Tampilkan hasil
    st.dataframe(
        merged[[
            'tgl_transaksi', 'jns_transaksi', 'nm_unit',
            'Kode Akun', 'Nama Akun', 'debet', 'kredit', 'uraian'
        ]],
        use_container_width=True
    )
    
    # Download option
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        merged.to_excel(writer, index=False)
    st.download_button(
        "Unduh Hasil Filter",
        output.getvalue(),
        file_name="hasil_filter.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def filter_data():
    """Fungsi utama untuk filtering data dengan optimasi"""
    st.title("Filter Data Transaksi - Optimized")

    # Muat data dengan progress indicator
    with st.spinner('Memuat data...'):
        bukubesar, coa = load_data()
        if bukubesar is None or coa is None:
            return

    # Widget filtering
    with st.form("filter_form"):
        # 1. Filter Bulan
        st.subheader("Pilih Rentang Bulan")
        bulan_min = bukubesar['tgl_transaksi'].dt.month.min()
        bulan_max = bukubesar['tgl_transaksi'].dt.month.max()
        selected_month = st.slider(
            "Bulan Transaksi",
            min_value=int(bulan_min),
            max_value=int(bulan_max),
            value=(int(bulan_min), int(bulan_max))
        )

        # 2. Filter Jenis Transaksi
        jns_options = bukubesar['jns_transaksi'].unique().tolist()
        selected_jns = st.multiselect(
            "Jenis Transaksi",
            options=jns_options,
            default=jns_options
        )

        # 3. Filter Unit
        unit_options = ["Semua"] + bukubesar['nm_unit'].dropna().unique().tolist()
        selected_unit = st.selectbox("Unit/SKPD", options=unit_options)

        # 4. Filter Level dan Kategori
        st.subheader("Filter Akun")
        col1, col2 = st.columns(2)
        with col1:
            selected_level = st.selectbox(
                "Level Akun",
                options=[f"Level {i}" for i in range(1, 7)]
            )
        with col2:
            kategori_options = {
                "PENDAPATAN DAERAH": "4",
                "BELANJA DAERAH": "5",
                "PEMBIAYAAN DAERAH": "6",
                "ASET": "1",
                "KEWAJIBAN": "2",
                "EKUITAS": "3"
            }
            selected_kategori = st.selectbox(
                "Kategori Akun",
                options=list(kategori_options.keys())
            )

        # 5. Filter Akun Spesifik
        target_level = int(selected_level.split()[-1])
        base_code = kategori_options[selected_kategori]

        # Filter COA berdasarkan level dan kategori
        filtered_coa = coa[
            (coa['Kode Akun'].str.startswith(base_code)) &
            (coa['Level'] == target_level)
        ]

        if not filtered_coa.empty:
            selected_akun = st.selectbox(
                "Pilih Akun",
                options=filtered_coa['Nama Akun'].unique()
            )
            kode_akun = filtered_coa.loc[
                filtered_coa['Nama Akun'] == selected_akun,
                'Kode Akun'
            ].iloc[0]
        else:
            st.warning("Tidak ada akun tersedia untuk kombinasi ini")
            return

        # Submit form
        submitted = st.form_submit_button("Proses Filter")

    if submitted:
        try:
            # Terapkan filter
            with st.spinner('Memproses data...'):
                filtered_data = apply_filters(
                    bukubesar, coa, selected_month, selected_jns, selected_unit, kode_akun
                )
            
            # Validasi hasil filter
            if validate_input(filtered_data):
                display_results(filtered_data, coa)
        
        except Exception as e:
            st.error(f"Terjadi kesalahan: {str(e)}")

def app():
    filter_data()

if __name__ == "__main__":
    app()
