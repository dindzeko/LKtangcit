import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

@st.cache_data
def load_data():
    # Load data bukubesar
    bukubesar = pd.read_excel('bukubesar.xlsb', engine='pyxlsb')
    
    # Load data COA
    coa = pd.read_excel('coa.xlsx')
    
    # Proses data COA untuk level 6
    coa_level6 = coa[coa['Level'] == 6].copy()
    
    # Split kode akun menjadi level 1-6
    coa_level6['kode_split'] = coa_level6['Kode Akun'].apply(lambda x: x.split('.'))
    for i in range(1, 7):
        coa_level6[f'level_{i}'] = coa_level6['kode_split'].apply(
            lambda parts: '.'.join(parts[:i]) if len(parts) >= i else ''
        )
    
    # Merge dengan bukubesar
    merged_df = pd.merge(
        bukubesar, 
        coa_level6[['Kode Akun', 'Nama Akun'] + [f'level_{i}' for i in range(1,7)]],
        left_on='kd_lv_6',
        right_on='Kode Akun',
        how='left'
    )
    
    # Konversi tipe data tanggal
    merged_df['tgl_transaksi'] = pd.to_datetime(merged_df['tgl_transaksi'])
    
    return merged_df

def app():
    st.title('Filter Data Transaksi')
    
    # Load data
    df = load_data()
    
    # Sidebar untuk filter
    st.sidebar.header("Parameter Filter")
    
    # Filter bulan
    selected_month = st.sidebar.slider(
        'Pilih Bulan Transaksi',
        1, 12,
        value=datetime.now().month
    )
    
    # Filter jenis transaksi
    jns_options = df['jns_transaksi'].unique().tolist()
    selected_jns = st.sidebar.multiselect(
        'Jenis Transaksi',
        jns_options,
        default=jns_options
    )
    
    # Filter unit
    unit_filter = st.sidebar.radio(
        "Filter Unit", 
        ['Semua Unit', 'SKPD']
    )
    
    selected_units = []
    if unit_filter == 'SKPD':
        unit_options = df['nm_unit'].unique().tolist()
        selected_units = st.sidebar.multiselect(
            'Pilih Unit SKPD',
            unit_options
        )
    
    # Filter level kode akun
    selected_level = st.sidebar.selectbox(
        'Pilih Level Kode Akun',
        options=[1,2,3,4,5,6]
    )
    
    level_col = f'level_{selected_level}'
    level_options = df[level_col].dropna().unique().tolist()
    selected_code = st.sidebar.selectbox(
        f'Pilih Kode Level {selected_level}',
        options=level_options
    )
    
    # Filter debit/kredit
    dk_filter = st.sidebar.radio(
        "Tipe Transaksi",
        ['Semua', 'Debet', 'Kredit']
    )
    
    # Terapkan filter
    filtered_df = df.copy()
    
    # Filter bulan
    filtered_df = filtered_df[filtered_df['tgl_transaksi'].dt.month == selected_month]
    
    # Filter jenis transaksi
    if selected_jns:
        filtered_df = filtered_df[filtered_df['jns_transaksi'].isin(selected_jns)]
    
    # Filter unit
    if unit_filter == 'SKPD' and selected_units:
        filtered_df = filtered_df[filtered_df['nm_unit'].isin(selected_units)]
    
    # Filter level kode
    filtered_df = filtered_df[filtered_df[level_col] == selected_code]
    
    # Filter debit/kredit
    if dk_filter == 'Debet':
        filtered_df = filtered_df[filtered_df['debet'] > 0]
    elif dk_filter == 'Kredit':
        filtered_df = filtered_df[filtered_df['kredit'] > 0]
    
    # Tampilkan hasil
    st.subheader("Data Hasil Filter")
    st.write(f"Jumlah Data Ditemukan: {len(filtered_df)}")
    st.dataframe(filtered_df.head(20))
    
    # Tombol download
    if not filtered_df.empty:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False)
        excel_data = output.getvalue()
        st.download_button(
            label="Unduh Data Filter",
            data=excel_data,
            file_name='data_filter.xlsx',
            mime='application/vnd.ms-excel'
        )

if __name__ == "__main__":
    app()
