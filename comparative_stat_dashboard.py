import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# ===========================
# CONFIG
# ===========================
st.set_page_config(page_title="Comparative Statistic Dashboard (Modern)", layout="wide")
st.title("🏨 Comparative Statistic Dashboard — Modern View")
st.markdown("Versi modern: tabel interaktif dan stylized dengan perhitungan Last Night, MTD, dan YTD.")

# ===========================
# PATH CSV
# ===========================
file_path = os.path.expanduser('~/Documents/newcopm/comparative_data.csv')
os.makedirs(os.path.dirname(file_path), exist_ok=True)

# ===========================
# SAFE LOAD CSV
# ===========================
required_cols = ['Date','Hotel','Room_Available','Room_Sold','ADR']
if os.path.exists(file_path):
    try:
        df = pd.read_csv(file_path, parse_dates=['Date'])
    except Exception as e:
        st.warning("File CSV ada tapi gagal dibaca. Membuat file baru dan mem-backup file lama.")
        # backup corrupted file
        try:
            bak = file_path + '.bak'
            os.replace(file_path, bak)
            st.info(f"File lama dipindah ke: {bak}")
        except Exception:
            pass
        df = pd.DataFrame(columns=required_cols)
        df.to_csv(file_path, index=False)
else:
    df = pd.DataFrame(columns=required_cols)
    df.to_csv(file_path, index=False)

# ensure required cols
for c in required_cols:
    if c not in df.columns:
        df[c] = None

# session state
if 'data' not in st.session_state:
    st.session_state.data = df.copy()

df = st.session_state.data.copy()

# ===========================
# INPUT FORM (only hotel data)
# ===========================
with st.sidebar.form('input_form'):
    st.write('## 📝 Input Data Harian')
    input_date = st.date_input('Tanggal', datetime.now().date())
    input_hotel = st.text_input('Nama Hotel', 'Daun Bali')
    input_room_available = st.number_input('Room Available', min_value=0, value=100, step=1)
    input_room_sold = st.number_input('Room Sold', min_value=0, value=0, step=1)
    input_adr = st.number_input('ADR (Average Rate)', min_value=0, value=0, step=1000)
    submitted = st.form_submit_button('Tambah Data')
    if submitted:
        new = pd.DataFrame({
            'Date': [pd.Timestamp(input_date)],
            'Hotel': [input_hotel],
            'Room_Available': [int(input_room_available)],
            'Room_Sold': [int(input_room_sold)],
            'ADR': [float(input_adr)]
        })
        st.session_state.data = pd.concat([st.session_state.data, new], ignore_index=True)
        st.session_state.data.to_csv(file_path, index=False)
        st.success('Data disimpan ke CSV.')
        df = st.session_state.data.copy()

# ===========================
# FILTER
# ===========================
st.sidebar.write('---')
selected_date = st.sidebar.date_input('Pilih tanggal untuk analisis', datetime.now().date())
selected_hotel = st.sidebar.selectbox('Pilih hotel (untuk fokus)', df['Hotel'].unique() if not df.empty else ['-'])

# helper functions

def aggregate_period(df_all, hotel=None, up_to_date=None, period='last'):
    """Return aggregated per-hotel DataFrame for given period type.
    period: 'last' -> snapshot at date; 'mtd' -> month-to-date up to date; 'ytd' -> year-to-date up to date
    If hotel provided, filter to that hotel only for result; otherwise return all hotels aggregated.
    """
    if df_all.empty:
        return pd.DataFrame()
    up_to = pd.Timestamp(up_to_date)
    if period == 'last':
        dfp = df_all[df_all['Date'] == up_to]
        grp = dfp.groupby('Hotel').agg({'Room_Available':'first','Room_Sold':'first','ADR':'first'})
        # compute revenue
        if not grp.empty:
            grp = grp.reset_index()
            grp['Revenue'] = grp['Room_Sold'] * grp['ADR']
        else:
            grp = pd.DataFrame(columns=['Hotel','Room_Available','Room_Sold','ADR','Revenue'])
    else:
        if period == 'mtd':
            dfp = df_all[(df_all['Date'].dt.month == up_to.month) & (df_all['Date'] <= up_to) & (df_all['Date'].dt.year==up_to.year)]
        elif period == 'ytd':
            dfp = df_all[(df_all['Date'].dt.year == up_to.year) & (df_all['Date'] <= up_to)]
        else:
            dfp = pd.DataFrame()
        if dfp.empty:
            grp = pd.DataFrame(columns=['Hotel','Room_Available','Room_Sold','ADR','Revenue'])
        else:
            grp = dfp.groupby('Hotel').agg({'Room_Available':'sum','Room_Sold':'sum','ADR':lambda x: (x * dfp.loc[x.index,'Room_Sold']).sum() / dfp.loc[x.index,'Room_Sold'].sum() if dfp.loc[x.index,'Room_Sold'].sum()>0 else 0})
            grp = grp.reset_index()
            grp['Revenue'] = grp['Room_Sold'] * grp['ADR']
    if hotel is not None:
        grp = grp[grp['Hotel'] == hotel]
    return grp.reset_index(drop=True)


def compute_metrics_table(df_all, up_to_date, period):
    # aggregated per hotel for period
    agg = aggregate_period(df_all, up_to_date=up_to_date, period=period)
    if agg.empty:
        return pd.DataFrame()
    total_available = agg['Room_Available'].sum()
    total_sold = agg['Room_Sold'].sum()
    total_revenue = agg['Revenue'].sum()

    agg['Occ%'] = agg.apply(lambda r: (r['Room_Sold']/r['Room_Available']*100) if r['Room_Available']>0 else 0, axis=1)
    agg['ARR'] = agg.apply(lambda r: (r['Revenue']/r['Room_Sold']) if r['Room_Sold']>0 else 0, axis=1)
    agg['RevPAR'] = agg.apply(lambda r: (r['Revenue']/r['Room_Available']) if r['Room_Available']>0 else 0, axis=1)

    # compute compset metrics (excluding each hotel) by combining others
    comp_occ_list = []
    comp_adr_list = []
    comp_revpar_list = []
    for idx, row in agg.iterrows():
        others = agg[agg['Hotel'] != row['Hotel']]
        if others.empty:
            comp_occ_list.append(0)
            comp_adr_list.append(0)
            comp_revpar_list.append(0)
        else:
            o_avail = others['Room_Available'].sum()
            o_sold = others['Room_Sold'].sum()
            o_rev = others['Revenue'].sum()
            occ = (o_sold/o_avail*100) if o_avail>0 else 0
            adr = (o_rev/o_sold) if o_sold>0 else 0
            revpar = (o_rev/o_avail) if o_avail>0 else 0
            comp_occ_list.append(occ)
            comp_adr_list.append(adr)
            comp_revpar_list.append(revpar)
    agg['Comp_Occ'] = comp_occ_list
    agg['Comp_ARR'] = comp_adr_list
    agg['Comp_RevPAR'] = comp_revpar_list

    # indexes
    agg['MPI'] = agg.apply(lambda r: (r['Occ%']/r['Comp_Occ']*100) if r['Comp_Occ']>0 else 0, axis=1)
    agg['ARI'] = agg.apply(lambda r: (r['ARR']/r['Comp_ARR']*100) if r['Comp_ARR']>0 else 0, axis=1)
    agg['RGI'] = agg.apply(lambda r: (r['RevPAR']/r['Comp_RevPAR']*100) if r['Comp_RevPAR']>0 else 0, axis=1)

    # rank by RevPAR descending
    agg['Rank'] = agg['RevPAR'].rank(method='dense', ascending=False).astype(int)
    # fair share = room available / total available
    agg['Fair_Share'] = agg['Room_Available'] / total_available

    # order columns for display
    display_cols = ['Hotel','Room_Available','Room_Sold','Occ%','ARR','Revenue','RevPAR','RGI','Rank','MPI','ARI','Fair_Share']
    # ensure columns exist
    for c in display_cols:
        if c not in agg.columns:
            agg[c]=0
    return agg[display_cols].sort_values('Rank')

# ===========================
# BUILD TABLES
# ===========================
periods = {'Last Night':'last','Month To Date':'mtd','Year To Date':'ytd'}
cols = st.columns(1)

for title, p in periods.items():
    table_df = compute_metrics_table(df, selected_date, p)
    st.markdown('---')
    st.subheader(f"{title} — {selected_date}")
    if table_df.empty:
        st.info('Tidak ada data untuk periode ini.')
        continue

    # format numbers
    table_df_formatted = table_df.copy()
    table_df_formatted['Occ%'] = table_df_formatted['Occ%'].map('{:,.2f}%'.format)
    table_df_formatted['ARR'] = table_df_formatted['ARR'].map('Rp {:,.0f}'.format)
    table_df_formatted['Revenue'] = table_df_formatted['Revenue'].map('Rp {:,.0f}'.format)
    table_df_formatted['RevPAR'] = table_df_formatted['RevPAR'].map('Rp {:,.0f}'.format)
    table_df_formatted['RGI'] = table_df_formatted['RGI'].map('{:,.2f}'.format)
    table_df_formatted['MPI'] = table_df_formatted['MPI'].map('{:,.2f}'.format)
    table_df_formatted['ARI'] = table_df_formatted['ARI'].map('{:,.2f}'.format)
    table_df_formatted['Fair_Share'] = table_df_formatted['Fair_Share'].map('{:,.2%}'.format)

    # plotly table
    header_color = ['#2EC4B6']*len(table_df_formatted.columns)
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(table_df_formatted.columns), fill_color='#2EC4B6', align='center', font=dict(color='black', size=12)),
        cells=dict(values=[table_df_formatted[col] for col in table_df_formatted.columns], fill_color=[['#f7fbff' if i%2==0 else '#ffffff' for i in range(len(table_df_formatted))] for _ in table_df_formatted.columns], align='center'))
    ])
    fig.update_layout(margin=dict(l=5,r=5,t=5,b=5), height=300)
    st.plotly_chart(fig, use_container_width=True)

# ===========================
# DATA & DOWNLOAD
# ===========================
st.markdown('---')
st.subheader('📋 Database (raw)')
st.dataframe(df.sort_values('Date', ascending=False))

csv_data = df.to_csv(index=False).encode('utf-8')
st.download_button(label='💾 Unduh Data CSV', data=csv_data, file_name='comparative_data.csv', mime='text/csv')

st.caption('Modern dashboard dengan tampilan tabel interaktif. Jika ada penyesuaian warna/kolom, beri tahu saya.')


