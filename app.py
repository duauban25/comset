import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import os, sys
import tempfile

try:
    from pdf_report import generate_pdf_report
    import graphic_report
except ImportError as e:
    st.error(f"❌ Import error: {e}")
    st.stop()

# ===========================
# 🔧 BUNDLING SUPPORT FUNCTION
# ===========================
def resource_path(relative_path):
    """
    Mendapatkan path absolut ke resource (gambar, csv, dll)
    agar tetap bisa diakses setelah dibundle ke .exe / .app
    """
    try:
        base_path = sys._MEIPASS  # lokasi sementara saat dibundle
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ===========================
# DATA DIRECTORY RESOLUTION
# ===========================
def _is_writable(dir_path: str) -> bool:
    try:
        os.makedirs(dir_path, exist_ok=True)
        test_file = os.path.join(dir_path, ".write_test")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        return True
    except Exception:
        return False

def get_data_dir() -> str:
    # Priority order for data directory resolution
    # 1) Streamlit Cloud persistent storage (highest priority)
    mount_dir = "/mount/data"
    if _is_writable(mount_dir):
        return mount_dir
    # 2) Environment variable
    env_dir = os.environ.get("DATA_DIR")
    if env_dir and _is_writable(env_dir):
        return env_dir
    # 3) Streamlit secrets
    try:
        secrets_dir = st.secrets.get("DATA_DIR")  # type: ignore[attr-defined]
        if secrets_dir and _is_writable(secrets_dir):
            return secrets_dir
    except Exception:
        pass
    # 4) Current working directory
    cwd_dir = os.path.join(os.getcwd(), "data")
    if _is_writable(cwd_dir):
        return cwd_dir
    # 5) User Documents/compbaru (local development fallback)
    docs_dir = os.path.join(os.path.expanduser("~"), "Documents", "compbaru")
    if _is_writable(docs_dir):
        return docs_dir
    # 6) Temp directory (last resort)
    tmp_dir = os.path.join(tempfile.gettempdir(), "compbaru")
    os.makedirs(tmp_dir, exist_ok=True)
    return tmp_dir

# ===========================
# CONFIG
# ===========================
logo_path = resource_path("Daun_logo.jpg")
DATA_DIR = get_data_dir()
file_path = os.path.join(DATA_DIR, "comparative_data.csv")

icon_path = logo_path if os.path.exists(logo_path) else None
st.set_page_config(
    page_title="Comparative Statistic Dashboard (Modern)",
    page_icon=icon_path,
    layout="wide"
)
try:
    components.html("""
    <script src="https://cdn.tailwindcss.com"></script>
    """, height=0)
except Exception:
    # Ignore if CDN blocked on platform
    pass
col1, col2 = st.columns([1, 3])
with col1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=80)
with col2:
    st.markdown(
        """
        <div class="pt-2">
          <h2 class="text-2xl font-semibold text-emerald-800">CompSet Dashboard — Daun Bali Seminyak</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
st.markdown("<div class='my-3 border-b border-emerald-300'></div>", unsafe_allow_html=True)
st.markdown("""
<h3 class="text-lg font-semibold text-emerald-800 mb-2">🖨️ Export Comparative Report to PDF</h3>
""", unsafe_allow_html=True)
st.markdown("<div class='mx-auto max-w-screen-2xl px-4 py-2'>", unsafe_allow_html=True)

# DIAGNOSTIC INFO
with st.expander("🔍 System Diagnostic Info"):
    st.write(f"**Current DATA_DIR**: `{DATA_DIR}`")
    st.write(f"**Directory exists**: {os.path.exists(DATA_DIR)}")
    st.write(f"**Directory writable**: {_is_writable(DATA_DIR)}")
    st.write(f"**comparative_data.csv path**: `{file_path}`")
    st.write(f"**comparative_data.csv exists**: {os.path.exists(file_path)}")
    st.write(f"**room_capacity.csv path**: `{os.path.join(DATA_DIR, 'room_capacity.csv')}`")
    st.write(f"**room_capacity.csv exists**: {os.path.exists(os.path.join(DATA_DIR, 'room_capacity.csv'))}")
    if "/mount/data" in DATA_DIR:
        st.success("✅ Using Streamlit Cloud persistent storage")
    elif "Documents/compbaru" in DATA_DIR:
        st.warning("⚠️ Using local home directory (not persistent on Cloud)")
    else:
        st.info(f"ℹ️ Using custom directory: {DATA_DIR}")

# ===========================
# LOAD & PREPARE DATA
# ===========================
os.makedirs(os.path.dirname(file_path), exist_ok=True)

required_cols = ['Date', 'Hotel', 'Room_Available', 'Room_Sold', 'ADR']

# ===========================
# Baca File CSV
# ===========================
if os.path.exists(file_path):
    try:
        df = pd.read_csv(file_path, parse_dates=['Date'])
        st.success(f"✅ Data dimuat dari: {file_path} ({len(df)} records)")
    except Exception as e:
        st.warning(f"⚠️ File CSV gagal dibaca: {e}. Membuat file baru kosong.")
        df = pd.DataFrame(columns=required_cols)
        try:
            df.to_csv(file_path, index=False)
            st.info("✅ File comparative_data.csv kosong berhasil dibuat.")
        except Exception as write_err:
            st.error(f"❌ Gagal menulis CSV: {write_err}")
            st.stop()
else:
    st.info("📝 File comparative_data.csv tidak ditemukan. Membuat file baru...")
    df = pd.DataFrame(columns=required_cols)
    try:
        df.to_csv(file_path, index=False)
        st.success("✅ File comparative_data.csv berhasil dibuat.")
    except Exception as e:
        st.error(f"❌ Gagal membuat file CSV: {e}")
        st.error(f"❌ Path: {file_path}")
        st.error(f"❌ Directory: {DATA_DIR}")
        st.stop()

# Pastikan semua kolom wajib ada
for c in required_cols:
    if c not in df.columns:
        df[c] = None

# Pastikan kolom tanggal valid
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
if df["Date"].isnull().all():
    st.warning("⚠️ Tidak ada data tanggal valid di file CSV kamu. Pastikan kolom 'Date' berformat tanggal.")

# ===========================
# 🔄 Hitung Otomatis Room_Revenue
# ===========================
# Konversi ke angka agar tidak error
df["Room_Sold"] = pd.to_numeric(df.get("Room_Sold", 0), errors="coerce").fillna(0)
df["ADR"] = pd.to_numeric(df.get("ADR", 0), errors="coerce").fillna(0)

# Hitung otomatis Room_Revenue setiap kali file dibuka
df["Room_Revenue"] = df["Room_Sold"] * df["ADR"]

# (Opsional) Simpan hasil perhitungan ke file
try:
    df.to_csv(file_path, index=False)
    st.info("💾 Data berhasil diperbarui.")
except Exception as e:
    st.error(f"❌ Gagal menyimpan pembaruan ke CSV: {e}")
    st.stop()

# ===========================
# ROOM CAPACITY REFERENCE
# ===========================
capacity_path = os.path.join(DATA_DIR, 'room_capacity.csv')

#st.write(f"🔎 Mencari file di: {capacity_path}")
if os.path.exists(capacity_path):
    try:
        capacity_df = pd.read_csv(capacity_path)
    except Exception as e:
        st.warning(f"⚠️ Gagal membaca room_capacity.csv: {e}")
        capacity_df = pd.DataFrame(columns=['Hotel', 'Room_Available'])
else:
    st.warning("⚠️ File 'room_capacity.csv' tidak ditemukan. Buat file tersebut dengan kolom Hotel dan Room_Available.")
    sample_capacity = pd.DataFrame({
        'Hotel': ['Daun Bali Seminyak', "D'Prima Hotel Petitenget", 'Kamanya Petitenget',
                  'The Capital Seminyak', 'Paragon Seminyak', 'Liberta'],
        'Room_Available': [100, 50, 75, 120, 80, 60]
    })
    try:
        sample_capacity.to_csv(capacity_path, index=False)
        st.success("✅ File 'room_capacity.csv' dibuat otomatis dengan data sampel.")
        capacity_df = sample_capacity
    except Exception as e:
        st.error(f"❌ Gagal membuat room_capacity.csv: {e}")
        st.error(f"❌ Path: {capacity_path}")
        st.error(f"❌ Directory: {DATA_DIR}")
        capacity_df = pd.DataFrame(columns=['Hotel', 'Room_Available'])

# Pastikan hotels_list selalu ada
hotels_list = []

if not df.empty and 'Hotel' in df.columns:
    hotels_list = sorted(df['Hotel'].dropna().unique().tolist())
elif not capacity_df.empty and 'Hotel' in capacity_df.columns:
    hotels_list = sorted(capacity_df['Hotel'].dropna().unique().tolist())
else:
    hotels_list = ['Daun Bali Seminyak', "D'Prima Hotel Petitenget", 'Kamanya Petitenget',
                   'The Capital Seminyak', 'Paragon Seminyak', 'Liberta']


# ===========================
# SIDEBAR INPUT FORM
# ===========================
with st.sidebar.form('input_form'):
    st.write('## 📝 Input Data Harian')
    from datetime import datetime, timedelta
    input_date = st.date_input('Tanggal', datetime.now().date() - timedelta(days=1))
    input_hotel = st.selectbox('Nama Hotel', hotels_list)

    # Ambil Room_Available dari referensi
    default_capacity = capacity_df.loc[capacity_df['Hotel'] == input_hotel, 'Room_Available']
    if not default_capacity.empty:
        input_room_available = int(default_capacity.values[0])
    else:
        input_room_available = 0
        st.warning(f"⚠️ Tidak ada Room_Available untuk {input_hotel} di room_capacity.csv")

    st.number_input('Room Available (dari referensi)', value=input_room_available, disabled=True)
    input_room_sold = st.number_input('Room Sold', min_value=0, value=0, step=1)
    input_adr = st.number_input('ADR (Average Rate)', min_value=0, value=0, step=1000)
    submitted = st.form_submit_button('Tambah Data')

    if submitted:
        new = pd.DataFrame({
            'Date': [pd.Timestamp(input_date)],
            'Hotel': [input_hotel],
            'Room_Available': [input_room_available],
            'Room_Sold': [int(input_room_sold)],
            'ADR': [float(input_adr)]
        })
        df = pd.concat([df, new], ignore_index=True)
        df.to_csv(file_path, index=False)
        st.success(f'✅ Data untuk "{input_hotel}" berhasil disimpan dengan kapasitas otomatis {input_room_available} kamar.')


# ===========================
# UPLOAD CSV / EXCEL
# ===========================
st.sidebar.write('---')
st.sidebar.subheader("📤 Upload CSV/Excel")

uploaded_file = st.sidebar.file_uploader("Pilih file CSV/Excel", type=['csv', 'xlsx'])
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            new_df = pd.read_csv(uploaded_file)
        else:
            new_df = pd.read_excel(uploaded_file)

        missing = [c for c in required_cols if c not in new_df.columns]
        if missing:
            st.error(f"❌ Kolom wajib hilang pada file upload: {', '.join(missing)}")
        else:
            # Normalisasi tipe data
            new_df['Date'] = pd.to_datetime(new_df['Date'], errors='coerce')
            new_df['Room_Sold'] = pd.to_numeric(new_df.get('Room_Sold', 0), errors='coerce').fillna(0)
            new_df['ADR'] = pd.to_numeric(new_df.get('ADR', 0), errors='coerce').fillna(0)
            # Hitung Room_Revenue jika belum ada
            if 'Room_Revenue' not in new_df.columns:
                new_df['Room_Revenue'] = new_df['Room_Sold'] * new_df['ADR']

            df = pd.concat([df, new_df], ignore_index=True)
            df.to_csv(file_path, index=False)
            st.success(f"✅ File '{uploaded_file.name}' berhasil diunggah dan digabung ke database.")
    except Exception as e:
        st.error(f"❌ Gagal membaca file: {e}")

# ===========================
# AGGREGATION & METRICS
# ===========================
def aggregate_period(df_all, up_to_date=None, period='last'):
    if df_all.empty:
        return pd.DataFrame()
    df_all['Date'] = pd.to_datetime(df_all['Date'], errors='coerce')
    up_to = pd.Timestamp(up_to_date)

    if period == 'last':
        dfp = df_all[df_all['Date'] == up_to]
    elif period == 'mtd':
        dfp = df_all[(df_all['Date'].dt.month == up_to.month) &
                     (df_all['Date'].dt.year == up_to.year) &
                     (df_all['Date'] <= up_to)]
    elif period == 'ytd':
        dfp = df_all[(df_all['Date'].dt.year == up_to.year) &
                     (df_all['Date'] <= up_to)]
    else:
        return pd.DataFrame()

    if dfp.empty:
        return pd.DataFrame()

    grp = dfp.groupby('Hotel').agg({
        'Room_Available': 'sum',
        'Room_Sold': 'sum',
        'ADR': lambda x: (x * dfp.loc[x.index, 'Room_Sold']).sum() / dfp.loc[x.index, 'Room_Sold'].sum() if dfp.loc[x.index, 'Room_Sold'].sum() > 0 else 0
    }).reset_index()
    grp['Revenue'] = grp['Room_Sold'] * grp['ADR']
    return grp


def compute_metrics_table(df_all, up_to_date, period):
    agg = aggregate_period(df_all, up_to_date=up_to_date, period=period)
    if agg.empty:
        return pd.DataFrame()

    agg['Occ%'] = agg.apply(lambda r: (r['Room_Sold'] / r['Room_Available'] * 100) if r['Room_Available'] > 0 else 0, axis=1)
    agg['ARR'] = agg['ADR']
    agg['RevPAR'] = agg.apply(lambda r: (r['Revenue'] / r['Room_Available']) if r['Room_Available'] > 0 else 0, axis=1)

    total_available = agg['Room_Available'].sum()
    total_sold = agg['Room_Sold'].sum()
    total_revenue = agg['Revenue'].sum()
    total_adr = total_revenue / total_sold if total_sold > 0 else 0
    total_occ = total_sold / total_available * 100 if total_available > 0 else 0
    total_revpar = total_revenue / total_available if total_available > 0 else 0

    agg['RGI'] = agg['RevPAR'] / total_revpar * 100 if total_revpar > 0 else 0
    agg['MPI'] = agg['Occ%'] / total_occ * 100 if total_occ > 0 else 0
    agg['ARI'] = agg['ADR'] / total_adr * 100 if total_adr > 0 else 0
    agg['Fair_Share'] = agg['Room_Available'] / total_available if total_available > 0 else 0
    agg['Rank'] = agg['RevPAR'].rank(ascending=False, method='min').astype(int)

    total_row = pd.DataFrame({
        'Hotel': ['TOTAL'],
        'Room_Available': [total_available],
        'Room_Sold': [total_sold],
        'ADR': [total_adr],
        'Revenue': [total_revenue],
        'Occ%': [total_occ],
        'ARR': [total_adr],
        'RevPAR': [total_revpar],
        'RGI': [100],
        'MPI': [100],
        'ARI': [100],
        'Fair_Share': [1],
        'Rank': [None]
    })

    agg = pd.concat([agg, total_row], ignore_index=True)
    agg = agg.sort_values(by=['Rank'], na_position='last')
    return agg

# ===========================
# PDF EXPORT SECTION
# ===========================
if not df.empty:
    st.markdown("""
    <p style='font-size:14px; color:#2E7D32; margin-bottom:0;'>
    🗓️ <b>Pilih Tanggal untuk Generate PDF</b>
    </p>
    """, unsafe_allow_html=True)
    st.markdown("<div class='bg-white rounded-xl border border-emerald-200 shadow-sm p-4 md:p-6 mb-6'>", unsafe_allow_html=True)

    all_dates = sorted(df["Date"].dropna().unique(), reverse=False)
    if len(all_dates) == 0:
        st.info("Tidak ada tanggal valid di dataset.")
    else:
        min_date = pd.to_datetime(all_dates[0]).date()
        max_date = pd.to_datetime(all_dates[-1]).date()
        last_date = max_date
        selected_date = st.date_input(
            "📅 Pilih tanggal:",
            value=last_date,
            min_value=min_date,
            max_value=max_date
        )

        summary_data = {
            "Last_Night": compute_metrics_table(df, selected_date, "last"),
            "Month_to_Date": compute_metrics_table(df, selected_date, "mtd"),
            "Year_to_Date": compute_metrics_table(df, selected_date, "ytd")
        }

        # ===========================
        # BUTTON GENERATE PDF
        # ===========================
        if st.button("📄 Generate PDF Report"):
            try:
                pdf_buffer = generate_pdf_report(summary_data, pd.to_datetime(selected_date), logo_path=logo_path)

                # Validasi PDF kosong
                if pdf_buffer is None or pdf_buffer.getbuffer().nbytes == 0:
                    st.error("⚠️ PDF kosong — kemungkinan ada error di proses generate.")
                else:
                    st.success("✅ PDF berhasil dibuat, silakan unduh di bawah ini.")
                    st.download_button(
                        label="⬇️ Download Report (PDF)",
                        data=pdf_buffer,
                        file_name=f"CompSet_Report_{pd.to_datetime(selected_date).strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"❌ Terjadi error saat membuat PDF: {e}")

        st.markdown("</div>", unsafe_allow_html=True)



# ===========================
# DISPLAY TABLES
# ===========================
if not df.empty:
    periods = {'Last Night': 'last', 'Month To Date': 'mtd', 'Year To Date': 'ytd'}
    for title, p in periods.items():
        selected_date_ts = pd.to_datetime(selected_date)
        selected_date_str = selected_date_ts.strftime('%d %B %Y')  # contoh: 09 Oktober 2025

        table_df = compute_metrics_table(df, selected_date_ts, p)
        st.markdown("<div class='bg-white rounded-xl border border-emerald-200 shadow-sm p-4 md:p-6 mb-6'>", unsafe_allow_html=True)
        st.markdown(f"<h3 class='text-lg font-semibold text-emerald-800 mb-3'>{title} — {selected_date_str}</h3>", unsafe_allow_html=True)


        table_df_formatted = table_df.copy()
        badges = []
        for _, row in table_df.iterrows():
            if row.get('Hotel') == 'TOTAL':
                badges.append('Σ TOTAL')
            elif row.get('Rank') == 1:
                badges.append('🏆 TOP')
            else:
                badges.append('')
        # Sisipkan kolom Badge di posisi awal
        table_df_formatted.insert(0, 'Badge', badges)
        for col in ['Room_Available', 'Room_Sold']:
            table_df_formatted[col] = table_df_formatted[col].map('{:,.0f}'.format)
        for col in ['Revenue']:
            table_df_formatted[col] = table_df_formatted[col].map('Rp {:,.0f}'.format)
        for col in ['ADR', 'ARR', 'RevPAR']:
            table_df_formatted[col] = table_df_formatted[col].map('Rp {:,.0f}'.format)
        for col in ['Occ%']:
            table_df_formatted[col] = table_df_formatted[col].map('{:,.2f}%'.format)
        for col in ['RGI', 'MPI', 'ARI']:
            table_df_formatted[col] = table_df_formatted[col].map('{:,.2f}'.format)
        table_df_formatted['Fair_Share'] = table_df_formatted['Fair_Share'].map('{:,.2%}'.format)
        table_df_formatted['Rank'] = table_df_formatted['Rank'].fillna('').astype(str)

        cell_colors = []
        for _, row in table_df.iterrows():
            if row['Hotel'] == 'TOTAL':
                cell_colors.append('#fff2cc')
            elif row['Rank'] == 1:
                cell_colors.append('#d9ead3')
            else:
                cell_colors.append('#ffffff')

        fig = go.Figure(data=[go.Table(
            header=dict(values=list(table_df_formatted.columns),
                        fill_color='#2EC4B6',
                        align='center',
                        font=dict(color='black', size=12)),
            cells=dict(values=[table_df_formatted[col] for col in table_df_formatted.columns],
                       fill_color=[cell_colors for _ in table_df_formatted.columns],
                       align='center'))
        ])
        fig.update_layout(margin=dict(l=5, r=5, t=5, b=5), height=380)
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{p}")
        st.markdown("</div>", unsafe_allow_html=True)

# ===========================
# RAW DATA VIEW
# ===========================
st.markdown("<div class='bg-white rounded-xl border border-emerald-200 shadow-sm p-4 md:p-6 mb-6'>", unsafe_allow_html=True)
st.markdown("<h3 class='text-lg font-semibold text-emerald-800 mb-3'>📋 Database (Raw Data)</h3>", unsafe_allow_html=True)
st.dataframe(df.sort_values('Date', ascending=False))
csv_data = df.to_csv(index=False).encode('utf-8')
st.download_button(label='💾 Unduh Data CSV', data=csv_data, file_name='comparative_data.csv', mime='text/csv')
st.caption('Dashboard modern dengan baris TOTAL, Rank, dan highlight RevPAR tertinggi.')
st.markdown("</div>", unsafe_allow_html=True)

# ===========================
# EDIT / DELETE DATA SECTION
# ===========================
st.markdown("<div class='bg-white rounded-xl border border-emerald-200 shadow-sm p-4 md:p-6 mb-6'>", unsafe_allow_html=True)
st.markdown("<h3 class='text-lg font-semibold text-emerald-800 mb-3'>✏️ Edit atau Hapus Data</h3>", unsafe_allow_html=True)

if not df.empty:
    df_sorted = df.sort_values("Date", ascending=False)
    df_sorted["Display"] = df_sorted.apply(lambda x: f"{x['Date'].strftime('%d %b %Y')} — {x['Hotel']}", axis=1)
    selected_row = st.selectbox("Pilih data yang ingin diedit:", df_sorted["Display"].tolist())

    if selected_row:
        row_data = df_sorted[df_sorted["Display"] == selected_row].iloc[0]
        edit_date = st.date_input("Tanggal", row_data["Date"].date())
        edit_hotel = st.text_input("Hotel", row_data["Hotel"])
        edit_room_available = st.number_input("Room Available", min_value=0, value=int(row_data["Room_Available"]))
        edit_room_sold = st.number_input("Room Sold", min_value=0, value=int(row_data["Room_Sold"]))
        edit_adr = st.number_input("ADR", min_value=0.0, value=float(row_data["ADR"]))

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Simpan Perubahan"):
                idx = df_sorted[df_sorted["Display"] == selected_row].index[0]
                df.loc[idx, "Date"] = pd.Timestamp(edit_date)
                df.loc[idx, "Hotel"] = edit_hotel
                df.loc[idx, "Room_Available"] = edit_room_available
                df.loc[idx, "Room_Sold"] = edit_room_sold
                df.loc[idx, "ADR"] = edit_adr
                df.to_csv(file_path, index=False)
                st.success("✅ Data berhasil diperbarui. Silakan refresh halaman untuk melihat hasil.")
        with col2:
            if st.button("🗑️ Hapus Data"):
                idx = df_sorted[df_sorted["Display"] == selected_row].index[0]
                df.drop(index=idx, inplace=True)
                df.to_csv(file_path, index=False)
                st.warning("⚠️ Data telah dihapus. Silakan refresh halaman.")
else:
    st.info("Belum ada data untuk diedit.")
st.markdown("</div>", unsafe_allow_html=True)



# ============================================
# PDF Report Button (Versi Aman & Download)
# ============================================
 

def render_pdf_button(summary, show_pdf_button=True):
    """
    Tombol untuk generate & download PDF Report.
    Fungsi ini dipanggil dari dalam generate_graphic_report().
    """
    if not show_pdf_button:
        return

    st.markdown("---")
    st.sidebar.subheader("📄 Generate & Download PDF Report")

    # Tombol di sidebar (lebih rapi)
    if st.sidebar.button("📄 Generate Graphic PDF Report"):
        try:
            # Tentukan folder output
            output_folder = os.path.expanduser("~/Documents/compbaru")
            os.makedirs(output_folder, exist_ok=True)

            # Buat nama file unik
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"graphic_report_{timestamp}.pdf"
            pdf_path = os.path.join(output_folder, pdf_filename)

            # Buat PDF menggunakan fungsi dari pdf_report.py
            pdf_result = generate_graphic_pdf(summary)

            if pdf_result and os.path.exists(pdf_result):
                st.sidebar.success("✅ PDF report generated successfully!")
                st.sidebar.write(f"📂 Saved at: `{pdf_result}`")

                # Tombol download
                with open(pdf_result, "rb") as f:
                    st.sidebar.download_button(
                        label="⬇️ Download PDF Report",
                        data=f,
                        file_name=Path(pdf_result).name,
                        mime="application/pdf"
                    )
            else:
                st.sidebar.error("❌ Failed to generate PDF report. Check console for details.")

        except Exception as e:
            st.sidebar.error(f"⚠️ Error generating PDF: {e}")



# Tutup container utama
st.markdown("</div>", unsafe_allow_html=True)

# ===============================================
# app.py — Aplikasi utama Streamlit
# ===============================================
st.sidebar.title("📍 Navigation")
nav = st.sidebar.radio("Pilih Tampilan:", ["Dashboard", "Graphic Report"], index=0)
st.sidebar.markdown("<div class='border-b border-emerald-300 my-2'></div>", unsafe_allow_html=True)

if nav == "Graphic Report":
    graphic_report.generate_graphic_report(show_pdf_button=True)



# -----------------------------------------------
# TOMBOL UNTUK GRAPHIC REPORT
# -----------------------------------------------
#import graphic_report  # pastikan file ada di folder yang sama

#st.markdown("---")
#if st.button("📊 Open Graphic Dashboard"):
#    st.session_state["show_graphic"] = True

#if st.session_state.get("show_graphic", False):
#    graphic_report.generate_graphic_report(show_pdf_button=True)




# ===========================
# END OF FILE
# ===========================
# 🏗️ PYINSTALLER BUILD COMMAND (Mac)
# pyinstaller --onefile --windowed \
#   --add-data "daun_logo.jpg:." \
#   --add-data "comparative_data.csv:." \
#   --hidden-import pdf_report \
#   app.py
#
# 🪟 PYINSTALLER BUILD COMMAND (Windows)
# pyinstaller --onefile --windowed ^
#   --add-data "daun_logo.jpg;." ^
#   --add-data "comparative_data.csv;." ^
#   --hidden-import pdf_report ^
#   app.py
