import pandas as pd
import streamlit as st
from io import BytesIO
import requests
import matplotlib.pyplot as plt

# Inisialisasi session state untuk menyimpan filter
if 'filters' not in st.session_state:
    st.session_state.filters = {
        'selected_level': 'kd_lv_1',
        'selected_unit_type': 'nm_unit',
        'selected_units': [],
        'selected_accounts': [],
        'selected_month_range': ('Januari', 'Desember')
    }

# Judul aplikasi
st.title("Aplikasi Visualisasi Data Transaksi")

# ID file Google Drive
file_id = "1p2PYISBdkAdFIFf41chb5ltw39L35ztP"
url = f"https://drive.google.com/uc?export=download&id={file_id}"

# Fungsi untuk membaca data dari Google Drive
@st.cache_data
def load_data():
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = BytesIO(response.content)
            df = pd.read_csv(data, sep=',', encoding='utf-8')
            df['tgl_transaksi'] = pd.to_datetime(df['tgl_transaksi'], errors='coerce')
            
            # Simpan nilai unik kolom
            unique_cols = {
                'nm_unit': df['nm_unit'].dropna().unique().tolist(),
                'nm_sub_unit': df['nm_sub_unit'].dropna().unique().tolist(),
                'nm_lv_1': df['nm_lv_1'].dropna().unique().tolist(),
                'nm_lv_2': df['nm_lv_2'].dropna().unique().tolist(),
                'nm_lv_3': df['nm_lv_3'].dropna().unique().tolist(),
                'nm_lv_4': df['nm_lv_4'].dropna().unique().tolist(),
                'nm_lv_5': df['nm_lv_5'].dropna().unique().tolist(),
                'nm_lv_6': df['nm_lv_6'].dropna().unique().tolist()
            }
            return df, unique_cols
        else:
            st.error(f"Gagal memuat data. Status code: {response.status_code}")
            return None, None
    except Exception as e:
        st.error(f"Error saat memuat data: {e}")
        return None, None

# Memuat data dan nilai unik
df, unique_cols = load_data()

if df is not None:
    # Sidebar untuk navigasi
    menu = st.sidebar.selectbox("Menu", ["Filter Data", "Visualisasi"])

    # Menu 1: Filter Data
    if menu == "Filter Data":
        st.header("Filter Data")

        # Radio button untuk memilih kode level
        level_options = ["kd_lv_1", "kd_lv_2", "kd_lv_3", "kd_lv_4", "kd_lv_5", "kd_lv_6"]
        selected_level = st.radio(
            "Pilih Kode Level",
            level_options,
            index=level_options.index(st.session_state.filters['selected_level'])
        )
        st.session_state.filters['selected_level'] = selected_level

        account_column = selected_level.replace("kd_", "nm_")

        # Radio button untuk memilih tipe unit
        unit_options = ["nm_unit", "nm_sub_unit"]
        selected_unit_type = st.radio(
            "Pilih Tipe Unit",
            unit_options,
            index=unit_options.index(st.session_state.filters['selected_unit_type'])
        )
        st.session_state.filters['selected_unit_type'] = selected_unit_type

        # Multiselect untuk unit/sub unit
        selected_units = st.multiselect(
            f"Pilih {selected_unit_type}",
            unique_cols[selected_unit_type],
            default=st.session_state.filters['selected_units']
        )
        st.session_state.filters['selected_units'] = selected_units

        # Multiselect untuk nama akun
        account_key = selected_level.replace("kd_", "nm_")
        selected_accounts = st.multiselect(
            f"Pilih Nama Akun ({account_column})",
            unique_cols[account_key],
            default=st.session_state.filters['selected_accounts']
        )
        st.session_state.filters['selected_accounts'] = selected_accounts

        # Slider rentang bulan
        months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                  "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        month_map = {month: idx+1 for idx, month in enumerate(months)}
        
        selected_month_range = st.select_slider(
            "Pilih Rentang Bulan",
            options=months,
            value=st.session_state.filters['selected_month_range']
        )
        st.session_state.filters['selected_month_range'] = selected_month_range

        # Terapkan filter menggunakan .query()
        filtered_df = df.query(
            f"`{account_column}` in @selected_accounts and "
            f"`{selected_unit_type}` in @selected_units and "
            f"tgl_transaksi.dt.month >= {month_map[selected_month_range[0]]} and "
            f"tgl_transaksi.dt.month <= {month_map[selected_month_range[1]]}"
        )

        # Hitung total dan saldo
        total_debet = filtered_df['debet'].sum()
        total_kredit = filtered_df['kredit'].sum()
        saldo = total_debet - total_kredit

        # Tambahkan baris total dan saldo
        final_df = pd.concat([
            filtered_df,
            pd.DataFrame([{
                "nomor": "",
                "no_bukti": "",
                "tgl_transaksi": "",
                selected_unit_type: "",
                account_column: "Jumlah",
                "debet": total_debet,
                "kredit": total_kredit,
                "uraian": ""
            }]),
            pd.DataFrame([{
                "nomor": "",
                "no_bukti": "",
                "tgl_transaksi": "",
                selected_unit_type: "",
                account_column: "Saldo",
                "debet": saldo if saldo > 0 else 0,
                "kredit": abs(saldo) if saldo < 0 else 0,
                "uraian": ""
            }])
        ]).reset_index(drop=True)

        # Tampilkan data
        st.dataframe(final_df)

        # Download Excel
        @st.cache_data
        def convert_to_excel(df_):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_.to_excel(writer, index=False, sheet_name="Filtered_Data")
            output.seek(0)
            return output.getvalue()

        if not final_df.empty:
            excel_data = convert_to_excel(final_df)
            st.download_button(
                label="Download Data (Excel)",
                data=excel_data,
                file_name="filtered_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # Menu 2: Visualisasi
    elif menu == "Visualisasi":
        st.header("Visualisasi Data")
        
        # Gunakan filter yang sama dari session state
        filters = st.session_state.filters
        account_column = filters['selected_level'].replace("kd_", "nm_")
        
        # Terapkan filter
        filtered_df = df.query(
            f"`{account_column}` in @filters['selected_accounts'] and "
            f"`{filters['selected_unit_type']}` in @filters['selected_units'] and "
            f"tgl_transaksi.dt.month >= {month_map[filters['selected_month_range'][0]]} and "
            f"tgl_transaksi.dt.month <= {month_map[filters['selected_month_range'][1]]}"
        )

        # Visualisasi
        @st.cache_data
        def create_plot(df_):
            fig, ax = plt.subplots()
            df_.groupby('tgl_transaksi')[['debet', 'kredit']].sum().plot.bar(ax=ax)
            ax.set_title("Total Debet dan Kredit per Tanggal")
            ax.set_xlabel("Tanggal Transaksi")
            ax.set_ylabel("Jumlah")
            return fig

        if not filtered_df.empty:
            st.pyplot(create_plot(filtered_df))
        else:
            st.warning("Tidak ada data untuk divisualisasikan.")
