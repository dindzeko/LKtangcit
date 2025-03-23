import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from functools import lru_cache

# Konfigurasi awal
DATA_PATH = {
    'bukubesar': "data/bukubesar.xlsb",
    'coa': "data/coa.xlsx"
}

@st.cache_data(ttl=3600, show_spinner="Memuat data...")
def load_and_preprocess():
    """Muat dan praproses data dengan optimasi memori"""
    try:
        # 1. Load data dengan tipe data spesifik
        dtype_bukubesar = {
            'no_bukti': 'category',
            'jns_transaksi': 'category',
            'nm_unit': 'category',
            'kd_lv_6': 'category',
            'uraian': 'category'
        }
        
        # Baca file besar dengan chunksize jika diperlukan
        bukubesar = pd.read_excel(
            DATA_PATH['bukubesar'],
            engine='pyxlsb',
            dtype=dtype_bukubesar,
            parse_dates=['tgl_transaksi']
        )
        
        # 2. Proses data COA
        coa = pd.read_excel(
            DATA_PATH['coa'],
            dtype={'Kode Akun': 'category', 'Level': 'int8'}
        )
        
        # Praproses level kode akun
        coa_level6 = coa[coa['Level'] == 6].copy()
        split_codes = coa_level6['Kode Akun'].str.split('.', expand=True)
        for i in range(6):
            coa_level6[f'level_{i+1}'] = split_codes.iloc[:, :i+1].agg('.'.join, axis=1)
        
        # 3. Gabungkan data
        merged = pd.merge(
            bukubesar,
            coa_level6[['Kode Akun', 'Nama Akun'] + [f'level_{i+1}' for i in range(6)]],
            left_on='kd_lv_6',
            right_on='Kode Akun',
            how='left'
        )
        
        # 4. Optimasi memori
        numeric_cols = ['debet', 'kredit']
        merged[numeric_cols] = merged[numeric_cols].apply(pd.to_numeric, downcast='float')
        
        # Buat indeks untuk kolom yang sering difilter
        merged.set_index('tgl_transaksi', inplace=True)
        
        return merged
    
    except Exception as e:
        st.error(f"Gagal memuat data: {str(e)}")
        return pd.DataFrame()

def create_filters(df):
    """Buat UI komponen filter"""
    filters = {}
    
    with st.sidebar:
        st.header("Parameter Filter")
        
        # 1. Filter rentang tanggal
        min_date = df.index.min().date()
        max_date = df.index.max().date()
        date_range = st.date_input(
            "Rentang Tanggal",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        filters['start_date'] = pd.Timestamp(date_range[0])
        filters['end_date'] = pd.Timestamp(date_range[1])
        
        # 2. Filter jenis transaksi
        jns_options = df['jns_transaksi'].cat.categories.tolist()
        filters['jns_transaksi'] = st.multiselect(
            "Jenis Transaksi",
            options=jns_options,
            default=jns_options,
            max_selections=5
        )
        
        # 3. Filter unit
        unit_options = ['All'] + df['nm_unit'].cat.categories.tolist()
        filters['unit'] = st.selectbox(
            "Unit/SKPD",
            options=unit_options,
            index=0
        )
        
        # 4. Filter level akun
        level_options = [f"Level {i+1}" for i in range(6)]
        selected_level = st.selectbox(
            "Level Akun",
            options=level_options
        )
        filters['level'] = int(selected_level.split()[-1])
        
        # 5. Filter kategori akun
        kategori_options = {
            'PENDAPATAN DAERAH-LO': '7',
            'BEBAN DAERAH-LO': '8',
            'PENDAPATAN DAERAH': '4',
            'BELANJA DAERAH': '5',
            'PEMBIAYAAN DAERAH': '6',
            'ASET': '1',
            'KEWAJIBAN': '2',
            'EKUITAS': '3'
        }
        filters['kategori'] = st.selectbox(
            "Kategori Akun",
            options=list(kategori_options.keys())
        )
        filters['kode_kategori'] = kategori_options[filters['kategori']]
        
        # 6. Filter tipe transaksi
        filters['tipe_transaksi'] = st.radio(
            "Tipe Transaksi",
            options=['All', 'Debet', 'Kredit'],
            index=0
        )
    
    return filters

@lru_cache(maxsize=None)
def filter_data(df, filters):
    """Terapkan filter dengan optimasi query"""
    try:
        # 1. Filter dasar berdasarkan tanggal
        mask = (df.index >= filters['start_date']) & (df.index <= filters['end_date'])
        
        # 2. Filter jenis transaksi
        if filters['jns_transaksi']:
            mask &= df['jns_transaksi'].isin(filters['jns_transaksi'])
        
        # 3. Filter unit
        if filters['unit'] != 'All':
            mask &= df['nm_unit'] == filters['unit']
        
        # 4. Filter level dan kategori akun
        level_col = f'level_{filters["level"]}'
        if level_col in df.columns:
            mask &= df[level_col].str.startswith(filters['kode_kategori'])
        
        # 5. Filter tipe transaksi
        if filters['tipe_transaksi'] == 'Debet':
            mask &= df['debet'] > 0
        elif filters['tipe_transaksi'] == 'Kredit':
            mask &= df['kredit'] > 0
        
        return df[mask].copy()
    
    except Exception as e:
        st.error(f"Error dalam filtering: {str(e)}")
        return pd.DataFrame()

def app():
    st.title("📊 Aplikasi Filter Data Transaksi")
    
    # Muat data
    with st.spinner('Memuat data...'):
        df = load_and_preprocess()
        if df.empty:
            return
    
    # Buat filter
    filters = create_filters(df)
    
    # Terapkan filter
    with st.spinner('Memproses filter...'):
        filtered_df = filter_data(df, tuple(filters.items()))
    
    # Tampilkan hasil
    st.subheader(f"Hasil Filter ({len(filtered_df):,} transaksi)")
    
    # Tampilkan data
    cols_to_show = [
        'no_bukti', 'tgl_transaksi', 'jns_transaksi', 'nm_unit',
        'kd_lv_6', 'Nama Akun', 'debet', 'kredit', 'uraian'
    ]
    st.dataframe(
        filtered_df[cols_to_show].head(1000),
        height=600,
        use_container_width=True
    )
    
    # Opsi download
    if not filtered_df.empty:
        st.subheader("Ekspor Data")
        
        # Pilihan format
        export_format = st.radio(
            "Format File",
            options=['Parquet (Cepat)', 'Excel (Lambat)'],
            horizontal=True
        )
        
        if st.button("Unduh Data"):
            with st.spinner('Menyiapkan file...'):
                if export_format == 'Parquet (Cepat)':
                    output = BytesIO()
                    filtered_df.to_parquet(output, index=False)
                    ext = 'parquet'
                else:
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        filtered_df.to_excel(writer, index=False)
                    ext = 'xlsx'
                
                st.download_button(
                    label=f"Unduh {ext.upper()}",
                    data=output.getvalue(),
                    file_name=f"filtered_data.{ext}",
                    mime="application/octet-stream"
                )

# Jalankan aplikasi
if __name__ == "__main__":
    app()
