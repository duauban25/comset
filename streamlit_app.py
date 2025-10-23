import streamlit as st
import pandas as pd
import os
from pdf_report import create_pdf_report
from graphic_report import create_graphic_report

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

        # --- Generate Reports ---
        if st.button("Generate Graphic Report"):
            with st.spinner("Creating graphic report..."):
                create_graphic_report(df)
            st.success("Graphic report created successfully!")

        if st.button("Generate PDF Report"):
            with st.spinner("Creating PDF report..."):
                create_pdf_report(df)
            st.success("PDF report created successfully!")

    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    st.info("Please upload an Excel file to continue.")

# --- Footer ---
st.markdown("---")
st.caption("© 2025 Daun Hospitality Management | Streamlit Dashboard")

