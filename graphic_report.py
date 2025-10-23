# =========================================================
# graphic_report.py — Modul Visualisasi & PDF Generator
# =========================================================
import streamlit as st
import pandas as pd
import altair as alt
import os
from pathlib import Path
from datetime import datetime
from pdf_report import generate_graphic_pdf

# ---------------------------------
# Data directory helper (shared)
# ---------------------------------
def get_data_dir() -> str:
    try:
        dd = st.secrets.get("DATA_DIR")
        if dd:
            os.makedirs(dd, exist_ok=True)
            return dd
    except Exception:
        pass
    dd = os.environ.get("DATA_DIR")
    if dd:
        os.makedirs(dd, exist_ok=True)
        return dd
    dd = os.path.join(os.getcwd(), "data")
    os.makedirs(dd, exist_ok=True)
    return dd


# =========================================================
# Fungsi Utama: Generate Graphic Report
# =========================================================
def generate_graphic_report(show_pdf_button=True):
    st.title("📊 Comparative Graphic Report")
    st.markdown("<div class='mx-auto max-w-screen-2xl px-4 py-2'>", unsafe_allow_html=True)

    # ============================================
    # Load Data
    # ============================================
    data_path = Path(get_data_dir()) / "comparative_data.csv"
    if not data_path.exists():
        st.error("❌ File 'comparative_data.csv' tidak ditemukan di folder project.")
        return

    df = pd.read_csv(data_path)

    if "Room_Revenue" not in df.columns:
        rs = pd.to_numeric(df.get("Room_Sold", 0), errors="coerce").fillna(0)
        adr = pd.to_numeric(df.get("ADR", 0), errors="coerce").fillna(0)
        df["Room_Revenue"] = rs * adr

    required_cols = ["Date", "Hotel", "Room_Available", "Room_Sold", "ADR", "Room_Revenue"]
    if not all(col in df.columns for col in required_cols):
        st.error("❌ Kolom pada 'comparative_data.csv' tidak lengkap.")
        return

    # ============================================
    # Data Cleaning & Feature Engineering
    # ============================================
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Occupancy"] = (df["Room_Sold"] / df["Room_Available"]) * 100
    df["RevPAR"] = df["Room_Revenue"] / df["Room_Available"]

#    available_dates = sorted(df["Date"].dropna().unique())
#    selected_date = st.selectbox("📅 Pilih tanggal data:", available_dates, index=len(available_dates)-1)
#    df_selected = df[df["Date"] == selected_date]
    # Pastikan kolom Date sudah berbentuk datetime
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Ambil hanya tanggal unik tanpa waktu
    available_dates = sorted(df["Date"].dropna().dt.date.unique())
    if len(available_dates) == 0:
        st.error("Tidak ada tanggal valid pada data.")
        return
    min_date = available_dates[0]
    max_date = available_dates[-1]
    last_date = max_date
    selected_date = st.date_input(
        "📅 Pilih tanggal data:",
        value=last_date,
        min_value=min_date,
        max_value=max_date
    )

    # Filter dataframe berdasarkan tanggal terpilih
    df_selected = df[df["Date"].dt.date == selected_date]


    # ============================================
    # Agregasi per Hotel
    # ============================================
    summary = df_selected.groupby("Hotel").agg({
        "Room_Available": "sum",
        "Room_Sold": "sum",
        "Room_Revenue": "sum",
        "ADR": "mean",
        "Occupancy": "mean",
        "RevPAR": "mean"
    }).reset_index()

    # Total Compset
    total = {
        "Room_Available": summary["Room_Available"].sum(),
        "Room_Sold": summary["Room_Sold"].sum(),
        "Room_Revenue": summary["Room_Revenue"].sum(),
        "ADR": summary["ADR"].mean(),
        "Occupancy": (summary["Room_Sold"].sum() / summary["Room_Available"].sum()) * 100,
        "RevPAR": summary["Room_Revenue"].sum() / summary["Room_Available"].sum()
    }

    # Tambahkan Index: MPI, ARI, RGI, Fair Share
    summary["MPI"] = (summary["Occupancy"] / total["Occupancy"]) * 100
    summary["ARI"] = (summary["ADR"] / total["ADR"]) * 100
    summary["RGI"] = (summary["RevPAR"] / total["RevPAR"]) * 100
    summary["Market_Fair_Share"] = (summary["Room_Available"] / total["Room_Available"]) * 100

    # ============================================
    # Tampilkan Data Summary
    # ============================================
    st.subheader("📋 Summary by Hotel")
    st.markdown("<div class='bg-white rounded-xl border border-emerald-200 shadow-sm p-4 md:p-6 mb-6'>", unsafe_allow_html=True)
    st.dataframe(summary.style.format({
        "Occupancy": "{:.2f}",
        "RevPAR": "{:,.0f}",
        "ADR": "{:,.0f}",
        "MPI": "{:.1f}",
        "ARI": "{:.1f}",
        "RGI": "{:.1f}",
        "Market_Fair_Share": "{:.1f}"
    }))
    st.markdown("</div>", unsafe_allow_html=True)

    # ============================================
    # Charts Section
    # ============================================
    st.markdown("---")
    st.markdown("<div class='bg-white rounded-xl border border-emerald-200 shadow-sm p-4 md:p-6 mb-6'>", unsafe_allow_html=True)
    st.markdown("### 📈 Occupancy vs Compset")

    occ_chart = (
        alt.Chart(summary)
        .mark_bar(color="#1f77b4")
        .encode(
            x=alt.X("Hotel:N", title="Hotel"),
            y=alt.Y("Occupancy:Q", title="Occupancy (%)")
        )
        .properties(height=300)
    )

    occ_line = alt.Chart(pd.DataFrame({"Compset": [total["Occupancy"]]})).mark_rule(
        color="red"
    ).encode(y="Compset:Q")

    occ_combined = (occ_chart + occ_line).configure_axis(
        grid=True, gridColor="#e2e8f0", labelColor="#065f46", titleColor="#065f46"
    ).configure_legend(
        orient="top", labelColor="#065f46", titleColor="#065f46"
    ).properties(
        background="white"
    )
    st.altair_chart(occ_combined, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Revenue Chart
    st.markdown("<div class='bg-white rounded-xl border border-emerald-200 shadow-sm p-4 md:p-6 mb-6'>", unsafe_allow_html=True)
    st.markdown("### 💰 Revenue vs Total Compset Revenue")
    rev_chart = (
        alt.Chart(summary)
        .mark_bar(color="#2ca02c")
        .encode(
            x=alt.X("Hotel:N", title="Hotel"),
            y=alt.Y("Room_Revenue:Q", title="Revenue (IDR)")
        )
        .properties(height=300)
    )
    # Garis pembanding: rata-rata compset revenue per hotel
    avg_rev = float(total["Room_Revenue"]) / max(len(summary), 1)
    rev_line = alt.Chart(pd.DataFrame({"Compset": [avg_rev]})).mark_rule(color="red").encode(y="Compset:Q")
    rev_combined = (rev_chart + rev_line).configure_axis(
        grid=True, gridColor="#e2e8f0", labelColor="#065f46", titleColor="#065f46"
    ).configure_legend(
        orient="top", labelColor="#065f46", titleColor="#065f46"
    ).properties(
        background="white"
    )
    st.altair_chart(rev_combined, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Index Comparison (MPI, ARI, RGI)
    st.markdown("<div class='bg-white rounded-xl border border-emerald-200 shadow-sm p-4 md:p-6 mb-6'>", unsafe_allow_html=True)
    st.markdown("### 📊 Performance Index Comparison (MPI / ARI / RGI)")
    index_data = summary.melt(
        id_vars=["Hotel"], value_vars=["MPI", "ARI", "RGI"],
        var_name="Index", value_name="Value"
    )
    index_chart = (
        alt.Chart(index_data)
        .mark_bar()
        .encode(
            x=alt.X("Hotel:N"),
            y=alt.Y("Value:Q", title="Index (100 = Benchmark)"),
            color="Index:N"
        )
        .properties(height=300)
    )
    # Garis pembanding 100% per indeks (MPI/ARI/RGI) agar sewarna dengan bar dan legenda bersama
    bench_df = pd.DataFrame({"Index": ["MPI", "ARI", "RGI"], "Value": [100.0, 100.0, 100.0]})
    idx_line = (
        alt.Chart(bench_df)
        .mark_rule(strokeDash=[4, 4])
        .encode(
            y="Value:Q",
            color="Index:N"
        )
    )
    index_combined = (index_chart + idx_line).configure_axis(
        grid=True, gridColor="#e2e8f0", labelColor="#065f46", titleColor="#065f46"
    ).configure_legend(
        orient="top", labelColor="#065f46", titleColor="#065f46"
    ).properties(
        background="white"
    )
    st.altair_chart(index_combined, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Market Fair Share
    st.markdown("<div class='bg-white rounded-xl border border-emerald-200 shadow-sm p-4 md:p-6 mb-6'>", unsafe_allow_html=True)
    st.markdown("### 🌍 Market Fair Share (%)")
    fair_chart = (
        alt.Chart(summary)
        .mark_bar(color="#ff7f0e")
        .encode(
            x=alt.X("Hotel:N"),
            y=alt.Y("Market_Fair_Share:Q", title="Market Fair Share (%)")
        )
        .properties(height=300)
    )
    # Garis pembanding: rata-rata fair share compset
    avg_fair = 100.0 / max(len(summary), 1)
    fair_line = alt.Chart(pd.DataFrame({"Fair": [avg_fair]})).mark_rule(color="red").encode(y="Fair:Q")
    fair_combined = (fair_chart + fair_line).configure_axis(
        grid=True, gridColor="#e2e8f0", labelColor="#065f46", titleColor="#065f46"
    ).configure_legend(
        orient="top", labelColor="#065f46", titleColor="#065f46"
    ).properties(
        background="white"
    )
    st.altair_chart(fair_combined, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ============================================
    # Sidebar - Generate PDF
    # ============================================
    if show_pdf_button:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📄 Generate & Download PDF Report")

        if st.sidebar.button("📄 Generate Graphic PDF Report"):
            pdf_path = generate_graphic_pdf(summary, report_date=selected_date)
            if pdf_path and os.path.exists(pdf_path):
                st.sidebar.success("✅ PDF report generated successfully!")
                st.sidebar.write(f"📂 Saved at: `{pdf_path}`")

                with open(pdf_path, "rb") as f:
                    st.sidebar.download_button(
                        label="⬇️ Download PDF Report",
                        data=f,
                        file_name=Path(pdf_path).name,
                        mime="application/pdf"
                    )
            else:
                st.sidebar.error("❌ Failed to generate PDF report. Please check the log.")
    st.markdown("</div>", unsafe_allow_html=True)
