import streamlit as st
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
from pdf_report import generate_graphic_pdf
from graphic_report import generate_graphic_report

# --- Setup ---
st.set_page_config(page_title="Daun Hospitality Dashboard", layout="wide")

# --- Load logo ---
logo_path = "Daun_logo.jpg"
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)
else:
    st.sidebar.warning("Logo not found: Daun_logo.jpg")

st.sidebar.title("Daun Hospitality Management")
st.sidebar.write("Revenue Management Dashboard")

# --- Data Upload ---
st.header("📊 Upload Data")
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("File uploaded successfully!")
        st.dataframe(df, use_container_width=True)

        # --- Basic Info ---
        st.subheader("Data Overview")
        st.write(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")

        # --- Persist uploaded data for other modules ---
        # Save to data/comparative_data.csv so graphic_report can read it
        try:
            os.makedirs("data", exist_ok=True)
            save_path = os.path.join("data", "comparative_data.csv")
            df.to_csv(save_path, index=False)
            st.info(f"Saved uploaded data to {save_path} for downstream reports.")
        except Exception as e:
            st.warning(f"Could not save comparative_data.csv: {e}")

        # --- Generate Reports ---
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Generate Graphic Report (In-App)"):
                with st.spinner("Rendering graphic report view..."):
                    generate_graphic_report(show_pdf_button=True)
        with col_b:
            if st.button("Generate PDF Report (Graphic PDF)"):
                with st.spinner("Creating PDF report..."):
                    # Compute summary similar to graphic_report for current latest date
                    try:
                        df_work = df.copy()
                        df_work["Date"] = pd.to_datetime(df_work.get("Date"), errors="coerce")
                        df_work["Room_Sold"] = pd.to_numeric(df_work.get("Room_Sold", 0), errors="coerce").fillna(0)
                        df_work["Room_Available"] = pd.to_numeric(df_work.get("Room_Available", 0), errors="coerce").fillna(0)
                        df_work["ADR"] = pd.to_numeric(df_work.get("ADR", 0), errors="coerce").fillna(0)
                        df_work["Room_Revenue"] = df_work["Room_Sold"] * df_work["ADR"]

                        if df_work["Date"].notna().any():
                            selected_date = df_work["Date"].dropna().dt.date.max()
                        else:
                            selected_date = datetime.now().date()

                        df_sel = df_work[df_work["Date"].dt.date == selected_date]
                        if df_sel.empty:
                            df_sel = df_work

                        summary = df_sel.groupby("Hotel").agg({
                            "Room_Available": "sum",
                            "Room_Sold": "sum",
                            "Room_Revenue": "sum",
                            "ADR": "mean"
                        }).reset_index()

                        # Derived metrics
                        summary["Occupancy"] = (summary["Room_Sold"] / summary["Room_Available"]).replace([float('inf'), -float('inf')], 0) * 100
                        summary["RevPAR"] = (summary["Room_Revenue"] / summary["Room_Available"]).replace([float('inf'), -float('inf')], 0)

                        # Totals for indices
                        total = {
                            "Room_Available": summary["Room_Available"].sum(),
                            "Room_Sold": summary["Room_Sold"].sum(),
                            "Room_Revenue": summary["Room_Revenue"].sum(),
                            "ADR": summary["ADR"].mean(),
                            "Occupancy": (summary["Room_Sold"].sum() / max(summary["Room_Available"].sum(), 1)) * 100,
                            "RevPAR": summary["Room_Revenue"].sum() / max(summary["Room_Available"].sum(), 1)
                        }

                        summary["MPI"] = (summary["Occupancy"] / max(total["Occupancy"], 1e-9)) * 100
                        summary["ARI"] = (summary["ADR"] / max(total["ADR"], 1e-9)) * 100
                        summary["RGI"] = (summary["RevPAR"] / max(total["RevPAR"], 1e-9)) * 100
                        summary["Market_Fair_Share"] = (summary["Room_Available"] / max(total["Room_Available"], 1)) * 100

                        pdf_path = generate_graphic_pdf(summary, report_date=selected_date)
                        if pdf_path and os.path.exists(pdf_path):
                            st.success("PDF report generated!")
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    label="⬇️ Download PDF Report",
                                    data=f,
                                    file_name=Path(pdf_path).name,
                                    mime="application/pdf"
                                )
                        else:
                            st.error("Failed to generate PDF report. Check logs.")
                    except Exception as e:
                        st.error(f"Error creating PDF: {e}")

    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    st.info("Please upload an Excel file to continue.")

# --- Footer ---
st.markdown("---")
st.caption("© 2025 Daun Hospitality Management | Streamlit Dashboard")

